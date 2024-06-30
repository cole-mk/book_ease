# -*- coding: utf-8 -*-
#
#  glib_utils.py
#
#  This file is part of book_ease.
#
#  Copyright 2024 mark cole <mark@capstonedistribution.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
# pylint: disable=wrong-import-position
# disabled because gi.repository requires an import order that pylint dislikes.

"""
This module provides some Glib related functionality.

Some Glib functions are not available to language bindings but are useful,
such as Glib.idle_add_once().

Other Glib functionalities are broken out to the language bindings, but the
documentation is incomplete enough that it is more sensible to just re-implement
something similar in Python, e.g. GTask is reimplemented as AsyncWorker.
"""

import threading
from typing import Callable
import gi  # pylint: disable=unused-import; It's clearly used on the next line.
from gi.repository import GLib


def _g_idle_add(once: bool, callback: Callable, *cb_args, priority=GLib.PRIORITY_DEFAULT_IDLE, **cb_kwargs):
    """
    * This method wraps calls to GLib.idle_add with keyword arguments that can be passed
      to the callback.

    * This method also optionally wraps the callback with a False return value. This guarantees
      that if the once parameter is True, the callback will only be called a single time. If the
      once parameter is False, The callback's return value is handled by the GLib event loop
      in the normal way. True = continue. False or None return value = stop.

    * GLib.idle_add by itself only accepts one keyword argument, priority. It is consumed by GLib.idle_add
      and no keyword arguments get passed to the callback.

    Args:

        once: Flag to determine if the callback gets removed from the event loop after its first invocation.

        callback: Callback to be placed on the eventloop.

        cb_args: Positional arguments passed to the callback.

        priority: GLib priority with which the callback gets placed on the event loop.

        cb_kwargs: Keyword arguments passed to callback.
    """
    def callback_wrapper(callback: Callable, packed_args: tuple):
        once: bool = packed_args[0]
        cb_args: tuple = packed_args[1]
        cb_kwargs: dict = packed_args[2]

        if once:
            callback(*cb_args, **cb_kwargs)
            return False
        else:
            return callback(*cb_args, **cb_kwargs)

    # Pack everything into a single tuple that can be handled by GLib.idle_add.
    packed_args = (once, cb_args, cb_kwargs)
    GLib.idle_add(callback_wrapper, callback, packed_args, priority=priority)


def g_idle_add_once(callback: Callable, *cb_args, priority=GLib.PRIORITY_DEFAULT_IDLE, **cb_kwargs):
    """
    * Place callback on the GLib event loop to be executed a single time.

    * Wrap GLib.idle_add() calls with a False return value so that the callback only fires once.

    * Wrap GLib.idle_add() calls with the ability to pass keyword arguments to the callback.

    Args:

        callback: Callback to be placed on the event loop.

        cb_args: Args passed to callback.

        priority: Keyword args that will be passed to GLib.idle_add,
            e.g. priority=GLib.PRIORITY_LOW

        cb_kwargs: Keyword args passed to callback. cb_kwargs key 'priority' is not
            allowed. It gets consumed by GLib.idle_add.
    """
    _g_idle_add(True, callback, *cb_args, priority=priority, **cb_kwargs)


def g_idle_add(callback: Callable, *args, priority=GLib.PRIORITY_DEFAULT_IDLE, **kwargs):
    """
    * Place callback on the GLib event loop to be executed until the callback returns False.

    * Wrap GLib.idle_add() calls with the ability to pass keyword arguments to the callback.

    Args:

        callback: Callback to be placed on the event loop.

        cb_args: Args passed to callback.

        priority: Keyword args that will be passed to GLib.idle_add,
            e.g. priority=GLib.PRIORITY_LOW.

        cb_kwargs: Keyword args passed to callback. cb_kwargs key 'priority' is not allowed. It
            gets consumed by GLib.idle_add.
    """
    _g_idle_add(False, callback, *args, priority=priority, **kwargs)


class AsyncWorkerCancelledError(RuntimeError):
    """A thread was cancelled"""


class AsyncWorker(threading.Thread):
    """
    * Run a function in a separate thread, calling an optional callback in the main context
      when that threaded function returns.

    * Subclasses threading.Thread

    * The thread is invoked in the same way as threading.Thread, call `AsyncWorker.start()`.

    * The constructor args/kwargs mirror those of `threading.Thread()`, but additionally takes
      the following arguments:

    Args:

        cancellable: Set to True to have a cancel_event (threading.Event) passed to the threaded
            function and the optional on_finished_cb.
            Note: The cancel_event will be appended to the end of args and cb_args and must be
            accounted for in their respective function declarations.

        on_finished_cb: Function to be called after the threaded function returns.
            The optional callback is executed in the main app context, meaning that this
            class is thread-safe from Gtk's point of view.

        cb_args: Args passed to on_finished_cb.

        pass_cancel_event_to_cb: If True, pass the cancel event (threading.Thread) as the last arg
            to the on_finished_cb.

    * An optional AsyncWorkerCancelledError is provided for run method implementors
      the raise if a worker thread is cancelled.

    * The following example assumes that the Glib event loop is already running.

    .. code-block:: python
        import time
        import glib_utils
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            import threading

        def run_after_thread_finished(some_cb_arg, cancel_event: threading.Event|None=None):
            if cancel_event is not None and cancel_event.is_set():
                print('threaded function was cancelled')
            else:
                print(f'threaded function finished: {some_cb_arg}')

        def threaded_function(some_arg, cancel_event: threading.Event|None=None):
            itr = 0
            while itr < 5:
                if cancel_event is not None and cancel_event.is_set():
                    return
                else:
                    time.sleep(1)
                    print(f'threaded_function {some_arg}')
                    itr +=1

        aw = AsyncWorker(target=threaded_function, args=('foo',), cancellable=True,
                          on_finished_cb=run_after_thread_finished, cb_args=('finished!!!',),
                          cb_kwargs=)

        aw2 = AsyncWorker(target=threaded_function, args=('foo2',), cancellable=True,
                          on_finished_cb=run_after_thread_finished, cb_args=('finished 2 !!!',))
        aw.start()
        aw2.start()
        time.sleep(2)
        aw.cancel()
        ...
        threaded_function foo
        threaded_function foo2
        threaded_function foo
        threaded_function foo2
        threaded_function foo
        threaded function was cancelled
        threaded_function foo2
        threaded_function foo2
        threaded_function foo2
        threaded function finished: finished 2 !!!
    """
    # pylint: disable=dangerous-default-value
    # disabled because this is just mirroring threading.Thread
    # If Pylint doesn't like it, Pylint is free to take it up with Python.

    def __init__(self, group=None, target=None,
                 name=None, args=(), kwargs={},
                 on_finished_cb: Callable=None, cb_args=(), cb_kwargs={},
                 cancellable:bool=False, pass_cancel_event_to_cb:bool=False,
                 pass_ret_val_to_cb:bool=False,*, daemon=None):
        super(AsyncWorker, self).__init__(group=group, target=target, name=name, daemon=daemon)
        self._cancellable = cancellable
        self._on_finished_cb = on_finished_cb
        self._kwargs = kwargs
        self._cb_args = [*cb_args]
        self._cb_kwargs = cb_kwargs
        self.pass_ret_val_to_cb = pass_ret_val_to_cb
        self._args = args
        if cancellable:
            self._cancel_event = threading.Event()
            self._kwargs['cancel_event'] = self._cancel_event
            if pass_cancel_event_to_cb:
                self._cb_args.append(self._cancel_event)
        else:
            self._cancel_event = None

    def run(self):
        """
        This function should not be called directly, use AsyncWorker.start().
        overrides: Thread.run()

        Start the threaded function. After completion of the threaded function
        call the optional callback.
        """
        if self._target:
            ret_val = self._target(*self._args, **self._kwargs)

        if self._on_finished_cb:
            if self.pass_ret_val_to_cb:
                self._cb_args.append(ret_val)
            g_idle_add_once(self._on_finished_cb, *self._cb_args, **self._cb_kwargs)

    def cancel(self):
        """
        Inform the threaded function that it has been cancelled.

        Raises: RuntimeError if the threaded function is not cancellable.
        """
        if self._cancel_event:
            self._cancel_event.set()
        else:
            raise RuntimeError('Attempted to cancel an uncancellable event.')
