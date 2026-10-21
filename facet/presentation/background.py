"""Work off the UI thread, and restarting the app."""
from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QProcess, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QApplication


class _Signals(QObject):
    done = Signal(object)
    failed = Signal(object)  # the exception


class _Worker(QRunnable):
    """Runs a network-only call off the UI thread."""

    def __init__(self, call):
        super().__init__()
        self.call = call
        self.signals = _Signals()

    def run(self):
        try:
            result = self.call()
        except Exception as e:  # reported on the UI thread; never crash the app
            self._send(self.signals.failed, e)
        else:
            self._send(self.signals.done, result)

    @staticmethod
    def _send(signal, value):
        try:
            signal.emit(value)
        except RuntimeError:
            pass  # the application closed while this was running


class _Receiver(QObject):
    """Lives on the UI thread, so the signals of a finished job are delivered there (a signal
    connected straight to a plain function would run it on the worker thread)."""

    def __init__(self, on_done, on_failed):
        super().__init__()
        self._on_done, self._on_failed = on_done, on_failed
        self.keep = None  # what to drop from `_alive` once the result has been handled

    @Slot(object)
    def done(self, result):
        _alive.discard(self.keep)
        self._on_done(result)

    @Slot(object)
    def failed(self, error):
        _alive.discard(self.keep)
        self._on_failed(error)


_alive: set = set()  # the Python side of a running job must outlive it, or its signals vanish


def run_in_background(call, on_done, on_failed) -> _Worker:
    worker = _Worker(call)
    receiver = _Receiver(on_done, on_failed)
    receiver.keep = (worker, receiver)
    _alive.add(receiver.keep)
    worker.signals.done.connect(receiver.done)
    worker.signals.failed.connect(receiver.failed)
    QThreadPool.globalInstance().start(worker)
    return worker


def restart_app():
    """Start a fresh Facet and quit this one (the window asks about unsaved changes)."""
    for window in QApplication.topLevelWidgets():
        if window.isWindow() and window.isVisible() and not window.close():
            return
    args = sys.argv[1:] if getattr(sys, "frozen", False) else sys.argv
    QProcess.startDetached(sys.executable, args)
    QApplication.quit()
