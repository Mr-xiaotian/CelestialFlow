import json
import threading
import requests
from multiprocessing import Value as MPValue
from typing import List, Optional, Dict, Any, Callable


class Client:
    """
    Python client for CelestialTree HTTP API.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 7777, timeout: float = 5.0):
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout

    def init_session(self):
        if hasattr(self, "session"):
            return

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def raise_for_status(self, r: requests.Response):
        if not (200 <= r.status_code < 300):
            raise RuntimeError(r.json()["error"])

    # ---------- Core APIs ----------

    def emit(
        self,
        type_: str,
        parents: Optional[List[int]] = None,
        message: Optional[str] = None,
        payload: Optional[bytes | dict] = None,
    ) -> int:
        """
        Emit a new event into CelestialTree.
        """
        self.init_session()

        body = {
            "type": type_,
            "parents": parents or [],
        }

        if message is not None:
            body["message"] = message

        if payload is not None:
            if isinstance(payload, (dict, list)):
                body["payload"] = json.dumps(payload).encode("utf-8")
            elif isinstance(payload, (bytes, bytearray)):
                body["payload"] = payload
            else:
                raise TypeError("payload must be bytes or dict")

        r = self.session.post(
            f"{self.base_url}/emit",
            data=json.dumps(body),
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()["id"]

    def get_event(self, event_id: int) -> Dict[str, Any]:
        self.init_session()

        r = self.session.get(
            f"{self.base_url}/event/{event_id}",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def children(self, event_id: int) -> List[int]:
        self.init_session()

        r = self.session.get(
            f"{self.base_url}/children/{event_id}",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def descendants(self, event_id: int, view: str = "struct") -> Dict[str, Any]:
        self.init_session()

        params = None
        if view and view != "struct":
            # 默认 struct 不传参，保持最干净也最兼容
            params = {"view": view}

        r = self.session.get(
            f"{self.base_url}/descendants/{event_id}",
            params=params,
            timeout=self.timeout,
        )

        if not (200 <= r.status_code < 300):
            # 有些错误响应可能不是 json，稍微做个兜底
            try:
                err = r.json().get("error", r.text)
            except Exception:
                err = r.text
            raise RuntimeError(err)

        return r.json()
    
    def ancestors(self, event_id: int) -> Dict[str, Any]:
        self.init_session()

        r = self.session.get(
            f"{self.base_url}/ancestors/{event_id}",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def heads(self) -> List[int]:
        self.init_session()

        r = self.session.get(
            f"{self.base_url}/heads",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()["heads"]

    def health(self) -> bool:
        self.init_session()
        try:
            r = self.session.get(
                f"{self.base_url}/healthz",
                timeout=self.timeout,
            )
            return r.status_code == 200
        except Exception:
            return False

    def version(self) -> Dict[str, Any]:
        self.init_session()

        r = self.session.get(
            f"{self.base_url}/version",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    # ---------- SSE Subscribe ----------

    def subscribe(
        self,
        on_event: Callable[[Dict[str, Any]], None],
        daemon: bool = True,
    ) -> threading.Thread:
        """
        Subscribe to SSE stream.
        on_event will be called for each emitted Event.
        """

        def _run():
            with self.session.get(
                f"{self.base_url}/subscribe",
                stream=True,
                timeout=None,
            ) as r:
                r.raise_for_status()
                buf = ""
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    if line.startswith("data:"):
                        data = line[len("data:") :].strip()
                        try:
                            ev = json.loads(data)
                            on_event(ev)
                        except Exception:
                            pass

        self.init_session()

        t = threading.Thread(target=_run, daemon=daemon)
        t.start()
        return t


class NullClient:
    def __init__(self, event_id=None):
        self.event_id = event_id if event_id is not None else MPValue("i", 0)

    def emit(self, *args, **kwargs):
        with self.event_id.get_lock():
            self.event_id.value += 1
            return self.event_id.value

    def get_event(self, *args, **kwargs):
        return None

    def children(self, *args, **kwargs):
        return []

    def descendants(self, *args, **kwargs):
        return None

    def heads(self):
        return []

    def subscribe(self, *args, **kwargs):
        return None
