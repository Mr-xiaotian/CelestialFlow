from __future__ import annotations

from typing import TYPE_CHECKING, List
from multiprocessing import Queue as MPQueue
from asyncio import Queue as AsyncQueue
from queue import Queue as ThreadQueue, Empty as SyncEmpty

from .envelope import TaskEnvelope
from .types import TerminationSignal

if TYPE_CHECKING:
    from ..persistence import LogSinker


class TaskInQueue:
    def __init__(
        self,
        queue: ThreadQueue | MPQueue | AsyncQueue,
        queue_tags: List[str],
        stage_tag: str,
        log_sinker: "LogSinker",
    ):
        self.queue = queue
        self.queue_tags = queue_tags
        self.stage_tag = stage_tag
        self.log_sinker = log_sinker
        self.direction = "in"
        self.termination_dict = {}

    def _log_put(self, item):
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        else:
            t = "unknown"
        self.log_sinker.put_item(t, item.id, item.source, self.stage_tag, self.direction)

    def _log_get(self, item):
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        else:
            t = "unknown"
        self.log_sinker.get_item(t, item.id, item.source, self.stage_tag)

    def add_source_tag(self, tag: str):
        if tag in self.queue_tags:
            raise ValueError(f"duplicate queue tag: {tag}")
        self.queue_tags.append(tag)

    def reset(self):
        self.termination_dict = {}

    def _normalize_source(self, source: str):
        if source == "input" and None in self.queue_tags:
            return None
        return source

    def _is_all_terminated(self) -> bool:
        return len(self.termination_dict) == len(self.queue_tags)

    def _merge_termination(self):
        return TerminationSignal(
            parents=list(self.termination_dict.values()),
            source=self.stage_tag,
        )

    def _record_termination(self, signal: TerminationSignal):
        source = self._normalize_source(signal.source)
        self.termination_dict[source] = signal.id

    def put(self, item: TaskEnvelope | TerminationSignal):
        try:
            self.queue.put(item)
            self._log_put(item)
        except Exception as e:
            self.log_sinker.put_item_error("in", self.stage_tag, self.direction, e)

    async def put_async(self, item: TaskEnvelope | TerminationSignal):
        try:
            if isinstance(self.queue, AsyncQueue):
                await self.queue.put(item)
            else:
                self.queue.put(item)
            self._log_put(item)
        except Exception as e:
            self.log_sinker.put_item_error("in", self.stage_tag, self.direction, e)

    def put_first(self, item: TaskEnvelope | TerminationSignal):
        self.put(item)

    async def put_first_async(self, item: TaskEnvelope | TerminationSignal):
        await self.put_async(item)

    def get(self) -> TaskEnvelope | TerminationSignal:
        while True:
            item: TaskEnvelope | TerminationSignal = self.queue.get()
            self._log_get(item)

            if isinstance(item, TaskEnvelope):
                return item

            if isinstance(item, TerminationSignal):
                self._record_termination(item)
                if self._is_all_terminated():
                    return self._merge_termination()
                continue

            raise ValueError(f"unexpected item type: {type(item)}")

    async def get_async(self) -> TaskEnvelope | TerminationSignal:
        while True:
            if isinstance(self.queue, AsyncQueue):
                item: TaskEnvelope | TerminationSignal = await self.queue.get()
            else:
                item = self.queue.get()

            self._log_get(item)

            if isinstance(item, TaskEnvelope):
                return item

            if isinstance(item, TerminationSignal):
                self._record_termination(item)
                if self._is_all_terminated():
                    return self._merge_termination()
                continue

            raise ValueError(f"unexpected item type: {type(item)}")

    def drain(self) -> List[TaskEnvelope]:
        results = []
        while True:
            try:
                item: TaskEnvelope | TerminationSignal = self.queue.get_nowait()
                self._log_get(item)
                if isinstance(item, TaskEnvelope):
                    results.append(item)
                elif isinstance(item, TerminationSignal):
                    self._record_termination(item)
            except SyncEmpty:
                break
            except Exception as e:
                self.log_sinker.get_item_error("in", self.stage_tag, self.direction, exception=e)
                break
        return results


class TaskOutQueue:
    def __init__(
        self,
        queue_list: List[ThreadQueue] | List[MPQueue] | List[AsyncQueue],
        queue_tags: List[str],
        stage_tag: str,
        log_sinker: "LogSinker",
    ):
        if len(queue_list) != len(queue_tags):
            raise ValueError("queue_list and queue_tags must have the same length")

        self.queue_list = queue_list
        self.queue_tags = queue_tags
        self.stage_tag = stage_tag
        self.log_sinker = log_sinker
        self.direction = "out"
        self._tag_to_idx = {tag: i for i, tag in enumerate(queue_tags)}

    def _log_put(self, item, idx: int):
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        else:
            t = "unknown"
        self.log_sinker.put_item(
            t, item.id, self.queue_tags[idx], self.stage_tag, self.direction
        )

    def add_queue(self, queue: ThreadQueue | MPQueue | AsyncQueue, tag: str):
        if tag in self._tag_to_idx:
            raise ValueError(f"duplicate queue tag: {tag}")
        self._tag_to_idx[tag] = len(self.queue_list)
        self.queue_list.append(queue)
        self.queue_tags.append(tag)

    def put(self, item: TaskEnvelope | TerminationSignal):
        for index, _ in enumerate(self.queue_list):
            self.put_channel(item, index)

    async def put_async(self, item: TaskEnvelope | TerminationSignal):
        for index, _ in enumerate(self.queue_list):
            await self.put_channel_async(item, index)

    def put_target(self, item: TaskEnvelope | TerminationSignal, tag: str):
        self.put_channel(item, self._tag_to_idx[tag])

    async def put_target_async(self, item: TaskEnvelope | TerminationSignal, tag: str):
        await self.put_channel_async(item, self._tag_to_idx[tag])

    def put_channel(self, item, idx: int):
        try:
            self.queue_list[idx].put(item)
            self._log_put(item, idx)
        except Exception as e:
            self.log_sinker.put_item_error(
                self.queue_tags[idx], self.stage_tag, self.direction, e
            )

    async def put_channel_async(self, item, idx: int):
        try:
            if isinstance(self.queue_list[idx], AsyncQueue):
                await self.queue_list[idx].put(item)
            else:
                self.queue_list[idx].put(item)
            self._log_put(item, idx)
        except Exception as e:
            self.log_sinker.put_item_error(
                self.queue_tags[idx], self.stage_tag, self.direction, e
            )
