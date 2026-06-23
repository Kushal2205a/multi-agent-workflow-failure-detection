import sys
import threading
import io


class _Capture:
    def __init__(self):
        self._buffer = io.StringIO()
        self._lock = threading.Lock()
        self._original = sys.stdout

    def write(self, text):
        with self._lock:
            self._buffer.write(text)
        self._original.write(text)

    def flush(self):
        with self._lock:
            self._buffer.flush()
        self._original.flush()

    def drain(self):
        with self._lock:
            content = self._buffer.getvalue()
            self._buffer = io.StringIO()
        return content


_capture = None
_lock = threading.Lock()


def install():
    global _capture
    with _lock:
        if _capture is None:
            _capture = _Capture()
            sys.stdout = _capture


def drain():
    global _capture
    if _capture is not None:
        return _capture.drain()
    return ""
