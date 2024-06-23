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

def poo():
    """
    doc_string
    """

def g_idle_add_once(callback, *cb_args, **g_kwargs):
    """
    Wrap GLib.idle_add() calls with a False return value so the callback only fires once.

    *cb_args: args passed to callback
    **g_kwargs: keyword args that will be passed to GLib.idle_add. ie priority=GLib.PRIORITY_LOW
    """
    def wrap_call_with_false_ret_value(callback, *cb_args):
        # I don't think that any kwargs get passed to the callback by GLib.idle_add
        # so they're not included here.
        callback(*cb_args)
        return False

    # I think that the only kwarg that GLib.idle_add accepts is 'priority'.
    GLib.idle_add(wrap_call_with_false_ret_value, callback, *cb_args, **g_kwargs)


class AsyncWorker(threading.Thread):
    """
    Run a function in a separate thread, calling an optional callback in the main context
    when that threaded function returns.
    The thread is invoked in the same way as threading.Thread, call `AsyncWorker.start()`.

    The constructor args/kwargs mirror those of `threading.Thread()`, but additionally takes
    the following arguments:

        cancellable: Set to True to have a cancel_event (threading.Event) passed to the threaded
            function and the optional on_finished_cb.
            Note: The cancel_event will be appended to the end of args and cb_args and must be
            accounted for in their respective function declarations.

        on_finished_cb: Function to be called after the threaded function returns.
            The optional callback is executed in the main app context, meaning that this
            class is thread-safe from Gtk's point of view.

        cb_args: Args passed to on_finished_cb

    **Note**: The following example assumes that the Glib event loop is already running.

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
                          on_finished_cb=run_after_thread_finished, cb_args=('finished!!!',))

        aw2 = AsyncWorker(target=threaded_function, args=('foo2',), cancellable=True,
                          on_finished_cb=run_after_thread_finished, cb_args=('finished!!!',))
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
        threaded function finished: finished!!!
    """
    # pylint: disable=dangerous-default-value
    # disabled because this is just mirroring threading.Thread
    # If Pylint doesn't like it, Pylint is free to take it up with Python.

    def __init__(self, group=None, target=None,
                 name=None, args=(), kwargs={},
                 on_finished_cb: Callable=None, cb_args=(),
                 cancellable:bool=False, *, daemon=None):

        threading.Thread.__init__(self, group=group, target=target, name=name, daemon=daemon)

        self._cancellable = cancellable
        self._on_finished_cb = on_finished_cb
        self._kwargs = kwargs
        if cancellable:
            self._cancel_event = threading.Event()
            self._args = (*args, self._cancel_event)
            self._cb_args = (*cb_args, self._cancel_event)
        else:
            self._cancel_event = None
            self._args = args
            self._cb_args = cb_args

    def run(self):
        """
        This function should not be called directly, use AsyncWorker.start().
        overrides: Thread.run()

        Start the threaded function. After completion of the threaded function
        call the optional callback.
        """
        if self._target:
            self._target(*self._args, **self._kwargs)
        if self._on_finished_cb:
            # self._on_finished_cb must run in the main context.
            # Glib.idle_add does not seem to take kwargs, so they're not included here.
            g_idle_add_once(self._on_finished_cb, *self._cb_args)

    def cancel(self):
        """
        Inform the threaded function that it has been cancelled.

        Raises: RuntimeError if the threaded function is not cancellable.
        """
        if self._cancel_event:
            self._cancel_event.set()
        else:
            raise RuntimeError('Attempted to cancel an uncancellable event.')
