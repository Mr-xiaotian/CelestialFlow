import json
import threading
import requests
from typing import List, Optional, Dict, Any, Callable


class Client:
    """
    Python client for CelestialTree HTTP API.
    """

    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def init_session(self):
        if hasattr(self, "session"):
            return
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    # ---------- Core APIs ----------

    def emit(
        self,
        type_: str,
        parents: Optional[List[int]] = None,
        message: Optional[str] = None,
        payload: Optional[bytes | dict] = None
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
        r.raise_for_status()
        return r.json()["id"]

    def get_event(self, event_id: int) -> Dict[str, Any]:
        self.init_session()
            
        r = self.session.get(
            f"{self.base_url}/event/{event_id}",
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def children(self, event_id: int) -> List[int]:
        self.init_session()
            
        r = self.session.get(
            f"{self.base_url}/children/{event_id}",
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()["children"]

    def descendants(self, event_id: int) -> Dict[str, Any]:
        self.init_session()
            
        r = self.session.get(
            f"{self.base_url}/descendants/{event_id}",
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def heads(self) -> List[int]:
        self.init_session()
            
        r = self.session.get(
            f"{self.base_url}/heads",
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()["heads"]

    def health(self) -> bool:
        self.init_session()
            
        r = self.session.get(
            f"{self.base_url}/healthz",
            timeout=self.timeout,
        )
        return r.status_code == 200

    def version(self) -> Dict[str, Any]:
        self.init_session()
            
        r = self.session.get(
            f"{self.base_url}/version",
            timeout=self.timeout,
        )
        r.raise_for_status()
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
                        data = line[len("data:"):].strip()
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
    def emit(self, *args, **kwargs):
        return None

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
