import asyncio
import logging
import subprocess
import threading
from queue import Queue, Empty

__version__ = "0.3.0"

class SubprocessLogCollector:

    def __init__(self, stdout_level=logging.INFO, stderr_level=logging.ERROR):
        """
        Create a log collector for subprocesses.
        :param stdout_level: global log level for stdout, default=INFO
        :param stderr_level: global log level for stderr, default=ERROR
        """
        self.queue = Queue()
        self.stdout_level = stdout_level
        self.stderr_level = stderr_level
        self._stop = False
        self._loop = asyncio.new_event_loop()
        self._dispatcher_done = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def attach(self, proc: subprocess.Popen, logger_name="subprocess",
               stdout_level=None, stderr_level=None):
        """
        Attach a subprocess to this collector.
        :param proc: subprocess.Popen object
        :param logger_name: logger name used for this subprocess
        :param stdout_level: override log level for stdout (optional)
        :param stderr_level: override log level for stderr (optional)
        """
        logger = logging.getLogger(logger_name)

        out_level = stdout_level if stdout_level is not None else self.stdout_level
        err_level = stderr_level if stderr_level is not None else self.stderr_level

        async def _reader(stream, level, prefix):
            loop = asyncio.get_event_loop()
            while True:
                line = await loop.run_in_executor(None, stream.readline)
                if not line:
                    break
                msg = line.decode(errors="replace").rstrip()
                self.queue.put((logger, level, f"[{prefix}] {msg}"))
            stream.close()

        async def _run_readers():
            tasks = []
            if proc.stdout:
                tasks.append(_reader(proc.stdout, out_level, logger_name))
            if proc.stderr:
                tasks.append(_reader(proc.stderr, err_level, logger_name))
            await asyncio.gather(*tasks)

        self._loop.call_soon_threadsafe(
            lambda: asyncio.ensure_future(_run_readers(), loop=self._loop)
        )

    async def _dispatcher(self):
        """Core loop to forward logs to Python log handler"""
        while not self._stop:
            try:
                logger, level, msg = await self._loop.run_in_executor(
                    None, self.queue.get, True, 0.5
                )
                logger.log(level, msg)
            except Empty:
                continue
        self._dispatcher_done.set()

    def _run(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._dispatcher())
        self._loop.close()

    def stop(self):
        """Stop collector gracefully."""
        self._stop = True
        self._dispatcher_done.wait()
        def shutdown():
            if self._loop.is_running():
                self._loop.stop()
        self._loop.call_soon_threadsafe(shutdown)
        self.thread.join()

def install(stdout_level=logging.INFO, stderr_level=logging.ERROR):
    """
    Install a subprocess log collector.
    Returns a collector instance.
    :param stdout_level: default log level for stdout
    :param stderr_level: default log level for stderr
    """
    return SubprocessLogCollector(stdout_level, stderr_level)
