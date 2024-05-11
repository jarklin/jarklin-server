# -*- coding=utf-8 -*-
r"""

"""
import time
import threading
import typing as t
from pathlib import Path
from watchdog import events
from watchdog.observers import Observer
if t.TYPE_CHECKING:
    from .types import PathSource


__all__ = ['WatchGod']


mutating_events: t.List[t.Type[events.FileSystemEvent]] = [
    events.FileDeletedEvent,
    events.FileModifiedEvent,
    events.FileCreatedEvent,
    events.FileMovedEvent,
    events.DirDeletedEvent,
    events.DirModifiedEvent,
    events.DirCreatedEvent,
    events.DirMovedEvent,
]


class WatchGod:
    r"""
    class to watch a directory for any changes but waits for filesystem events to calm down before reporting them

    >>> god = WatchGod(root=...)
    >>> god.start()
    >>> god.wait()
    >>> god.get_dirty()
    [...]
    """

    _observer: 'Observer'
    _quiet_time: float
    _dirty_lock: 'threading.Lock'
    _dirty: t.Set[Path]
    _last_event_lock: 'threading.Lock'
    _last_event: float

    def __init__(self, root: 'PathSource', *, quiet_time: float = 30.0):
        root = Path(root).expanduser().absolute()
        if not root.is_dir():
            raise NotADirectoryError(f"'{root!s}' is not a directory or does not exist")
        self._observer = Observer()
        self._observer.schedule(self, str(root), recursive=True, event_filter=mutating_events)

        self._quiet_time = quiet_time
        self._dirty_lock = threading.Lock()
        self._dirty = set()
        self._last_event_lock = threading.Lock()
        self._last_event = 0.0

    def __enter__(self) -> 'WatchGod':
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
        self.join()

    def start(self) -> None:
        r""" starts listening to filesystem-events """
        self._observer.start()

    def stop(self) -> None:
        r""" stops listening to filesystem-events """
        self._observer.stop()

    def join(self, *, timeout: float = None) -> None:
        r""" ensures it has stopped listening to filesystem-events """
        self._observer.join(timeout=timeout)

    def wait(self, *, timeout: float = None, poll_delay: float = None) -> None:
        r""" combination of wait_for_new_changes() and wait_events_calm_down() """
        start_time = time.time()
        self.wait_for_new_changes(timeout=timeout)
        now = time.time()
        timeout = start_time - now if timeout else None
        self.wait_events_calm_down(timeout=timeout, poll_delay=poll_delay)

    def wait_for_new_changes(self, *, timeout: float = None, poll_delay: float = None) -> None:
        r""" waits till any changes where detected """
        poll_delay = (self._quiet_time / 10) if poll_delay is None else poll_delay
        start_time = time.time()  # for timeout
        while True:
            now = time.time()
            if timeout and now > (start_time + timeout):
                raise TimeoutError(f"No new changed within the specified timeout of {timeout:.1}s")
            with self._dirty_lock:
                if self._dirty:
                    break
            time.sleep(poll_delay)

    def wait_events_calm_down(self, *, timeout: float = None, poll_delay: float = None) -> None:
        r""" waits till events have calmed down """
        poll_delay = (self._quiet_time / 10) if poll_delay is None else poll_delay
        start_time = time.time()  # for timeout
        while True:
            now = time.time()
            if timeout and now > (start_time + timeout):
                raise TimeoutError(f"Filesystem-Events didn't calm down in the specified timeout of {timeout:.1}s")
            with self._last_event_lock:
                if self._last_event + self._quiet_time < now:
                    break
            time.sleep(poll_delay)

    def get_dirty(self) -> t.List[Path]:
        r""" gets polluted files and directories since last calling this function """
        with self._dirty_lock:
            dirty = self._dirty.copy()
            self._dirty.clear()
        return list(dirty)

    def dispatch(self, event: events.FileSystemEvent) -> None:
        r""" internal usage only """
        with self._dirty_lock, self._last_event_lock:  # separated or together. no idea what's better
            self._dirty.add(Path(event.src_path))
            if event.dest_path:
                self._dirty.add(Path(event.dest_path))

            now = time.time()
            if now > self._last_event:
                self._last_event = now


if __name__ == '__main__':
    god = WatchGod("~/Downloads/")
    god.start()
    try:
        while True:
            print("Waiting for calmdown...")
            god.wait()
            print("Changes:", god.get_dirty())
    except KeyboardInterrupt:
        god.stop()
        god.join()
