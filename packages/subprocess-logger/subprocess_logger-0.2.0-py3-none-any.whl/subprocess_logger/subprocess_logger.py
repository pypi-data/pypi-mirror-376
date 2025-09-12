import logging
import subprocess
import threading
from queue import Queue, Empty

__version__ = "0.1.0"

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
        self._reader_threads = []   # track reader threads
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

        def _reader(stream, level, prefix):
            for line in iter(stream.readline, b''):
                msg = line.decode(errors="replace").rstrip()
                self.queue.put((logger, level, f"[{prefix}] {msg}"))
            stream.close()

        if proc.stdout:
            t = threading.Thread(
                target=_reader, args=(proc.stdout, out_level, logger_name), daemon=True
            )
            t.start()
            self._reader_threads.append(t)

        if proc.stderr:
            t = threading.Thread(
                target=_reader, args=(proc.stderr, err_level, logger_name), daemon=True
            )
            t.start()
            self._reader_threads.append(t)

    def _run(self):
        """Core loop to forward logs to Python log handler"""
        while not self._stop:
            try:
                logger, level, msg = self.queue.get(timeout=0.5)
                logger.log(level, msg)
            except Empty:
                continue

    def stop(self):
        """Stop collector gracefully.
        :param wait: if True, join reader and dispatcher threads
        """
        self._stop = True
        self.thread.join()
        for t in self._reader_threads:
            t.join()

def install(stdout_level=logging.INFO, stderr_level=logging.ERROR):
    """
    Install a subprocess log collector.
    Returns a collector instance.
    :param stdout_level: default log level for stdout
    :param stderr_level: default log level for stderr
    """
    return SubprocessLogCollector(stdout_level, stderr_level)
