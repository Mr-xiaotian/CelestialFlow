from __future__ import annotations

import json
from pathlib import Path
from time import localtime, strftime
from typing import Any, TextIO

from celestialflow.funnel import BaseInlet, BaseSpout


class JsonlSpout(BaseSpout):
    """Write queued records into a local JSONL file."""

    def __init__(self, output_path: str | Path) -> None:
        super().__init__()
        self.output_path = Path(output_path)
        self._file: TextIO | None = None
        self.handled_count = 0

    def _before_start(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.output_path.open("w", encoding="utf-8", buffering=1)
        self.handled_count = 0

    def _handle_record(self, record: dict[str, Any]) -> None:
        if self._file is None:
            raise RuntimeError("output file is not initialized")
        self._file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.handled_count += 1

    def _after_stop(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None


class EventInlet(BaseInlet):
    """A tiny event collector built on top of BaseInlet."""

    def emit(self, event: str, payload: Any) -> None:
        self._funnel(
            {
                "timestamp": strftime("%Y-%m-%d %H:%M:%S", localtime()),
                "event": event,
                "payload": payload,
            }
        )

    def info(self, message: str) -> None:
        self.emit("info", {"message": message})

    def metric(self, name: str, value: int | float) -> None:
        self.emit("metric", {"name": name, "value": value})


def demo_funnel_jsonl() -> None:
    output_path = Path("temp/demo_funnel/events.jsonl")
    spout = JsonlSpout(output_path)
    inlet = EventInlet(spout.get_queue())

    spout.start()
    try:
        inlet.info("funnel demo start")
        inlet.metric("processed", 3)
        inlet.emit(
            "batch_finished",
            {
                "items": ["A", "B", "C"],
                "success": True,
            },
        )
    finally:
        spout.stop()

    print(f"Output file: {output_path.resolve()}")
    print(f"Handled records: {spout.handled_count}")
    print(output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    demo_funnel_jsonl()
