from timeit import default_timer as timer
import asyncio, threading


def seconds_to_str(sec: float):
    minutes, seconds = divmod(sec, 60)
    minutes_s = f"{int(minutes)}min"
    seconds_s = f"{seconds:.1f}s"
    return f"{minutes_s} {seconds_s}" if minutes > 0 else seconds_s


class Timer:
    def __init__(self):
        self._start_time = None  # : float
        self.delta = None  # : float

    def start(self):
        self._start_time = timer()

    def stop(self):
        if self._start_time is None:
            raise Exception(f"Timer is not running. Use .start() to start it")

        self.delta = timer() - self._start_time
        self._start_time = None
        return self.delta

    def __str__(self):
        if self._start_time != None:
            return "running"
        if not self.delta:
            return "not started"
        return seconds_to_str(self.delta)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()


def async_wrap_iter(it):
    """Wrap blocking iterator into an asynchronous one.
    Not used ATM, but it's generally quite usefull in itself.

    https://stackoverflow.com/a/62297994
    """
    loop = asyncio.get_event_loop()
    q = asyncio.Queue(1)
    exception = None
    _END = object()

    async def yield_queue_items():
        while True:
            next_item = await q.get()
            if next_item is _END:
                break
            yield next_item
        if exception is not None:
            # the iterator has raised, propagate the exception
            raise exception

    def iter_to_queue():
        nonlocal exception
        try:
            for item in it:
                # This runs outside the event loop thread, so we
                # must use thread-safe API to talk to the queue.
                asyncio.run_coroutine_threadsafe(q.put(item), loop).result()
        except Exception as e:
            exception = e
        finally:
            asyncio.run_coroutine_threadsafe(q.put(_END), loop).result()

    threading.Thread(target=iter_to_queue).start()
    return yield_queue_items()
