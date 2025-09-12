import unittest
import logging
import subprocess
import sys
from io import StringIO
from subprocess_logger import SubprocessLogCollector

class TestSubprocessLogger(unittest.TestCase):

    def setUp(self):
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.logger = logging.getLogger("subprocess")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []
        self.logger.addHandler(self.handler)

    def tearDown(self):
        self.logger.handlers = []

    def _run_echo_subprocess(self, text, stderr=False):
        # Create a subprocess that writes to stdout or stderr
        if stderr:
            code = f"import sys; sys.stderr.write('{text}\\n')"
        else:
            code = f"print('{text}')"
        return subprocess.Popen(
            [sys.executable, "-c", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    def test_stdout_logging(self):
        collector = SubprocessLogCollector()
        proc = self._run_echo_subprocess("hello stdout")
        collector.attach(proc, logger_name="subprocess")
        proc.wait()
        collector.stop()
        logs = self.log_stream.getvalue()
        self.assertIn("hello stdout", logs)
        self.assertIn("[subprocess]", logs)

    def test_stderr_logging(self):
        collector = SubprocessLogCollector()
        proc = self._run_echo_subprocess("hello stderr", stderr=True)
        collector.attach(proc, logger_name="subprocess")
        proc.wait()
        collector.stop()
        logs = self.log_stream.getvalue()
        self.assertIn("hello stderr", logs)
        self.assertIn("[subprocess]", logs)

    def test_custom_log_levels(self):
        collector = SubprocessLogCollector(stdout_level=logging.WARNING, stderr_level=logging.CRITICAL)
        proc = self._run_echo_subprocess("warn stdout")
        collector.attach(proc, logger_name="subprocess")
        proc.wait()
        collector.stop()
        logs = self.log_stream.getvalue()
        self.assertIn("warn stdout", logs)

    def test_multiple_subprocesses(self):
        collector = SubprocessLogCollector()
        procs = [
            self._run_echo_subprocess(f"msg {i}") for i in range(3)
        ]
        for proc in procs:
            collector.attach(proc, logger_name="subprocess")
        for proc in procs:
            proc.wait()
        collector.stop()
        logs = self.log_stream.getvalue()
        for i in range(3):
            self.assertIn(f"msg {i}", logs)

    def test_attach_with_custom_logger_name(self):
        custom_logger_name = "custom_subprocess"
        custom_logger = logging.getLogger(custom_logger_name)
        custom_stream = StringIO()
        custom_handler = logging.StreamHandler(custom_stream)
        custom_logger.setLevel(logging.DEBUG)
        custom_logger.handlers = []
        custom_logger.addHandler(custom_handler)

        collector = SubprocessLogCollector()
        proc = self._run_echo_subprocess("custom logger")
        collector.attach(proc, logger_name=custom_logger_name)
        proc.wait()
        collector.stop()
        logs = custom_stream.getvalue()
        self.assertIn("custom logger", logs)
        self.assertIn("[custom_subprocess]", logs)

if __name__ == "__main__":
    unittest.main()