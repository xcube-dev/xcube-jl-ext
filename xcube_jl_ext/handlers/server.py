import subprocess
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

import jupyter_server.base.handlers
import psutil
import tornado.web

from ..config import default_server_config
from ..config import default_server_port
from ..config import is_jupyter_server_proxy_enabled
from ..config import server_config_file
from ..config import server_log_file

XcServerInfo = Tuple[Optional[psutil.Popen], Optional[int], List[str]]
XcServerOutput = Tuple[Optional[str], Optional[str]]


# noinspection PyAbstractClass
class ServerHandler(jupyter_server.base.handlers.APIHandler):
    """Manage a single xcube server process."""

    # @tornado.web.authenticated
    def get(self):
        """Respond with server's process state.
        If there is no current server process, respond with status code 404.
        """
        self.finish(self.xc_server_state)

    # @tornado.web.authenticated
    def put(self):
        """Start a new xcube server.
        If the server is already running, do nothing.
        Respond with server's process state.
        If the server could not be started, respond with status code 500.
        """
        self._start_server()
        self.finish(self.xc_server_state)

    # @tornado.web.authenticated
    def delete(self):
        """Terminate a running xcube server.
        Respond with server's process state.
        If there is no current server process, respond with status code 404.
        """
        self._stop_server()
        self.finish(self.xc_server_state)

    @property
    def xc_server_state(self) -> Dict[str, Any]:
        process, port, cmdline = self.xc_server_info
        if process is None:
            raise tornado.web.HTTPError(
                status_code=404,
                log_message='xcube server process not started yet.'
            )
        # if not process.is_running():
        #     raise tornado.web.HTTPError(
        #         status_code=404,
        #         log_message='xcube server could not be started.'
        #     )

        stdout, stderr = self.xc_server_output
        print(80 * "#")
        print(type(stdout), type(stderr))
        print(stdout)
        print(stderr)
        print(80 * "#")

        # TODO (forman): include stdout + stderr
        returncode = process.poll()
        server_state = {
            "port": port,
            "pid": process.pid,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
        for attr, default_value in [
            ("status", "gone"),
            ("cmdline", cmdline),
            ("name", None),
            ("username", None),
        ]:
            try:
                server_state[attr] = getattr(process, attr)()
            except psutil.NoSuchProcess:
                server_state[attr] = default_value

        import json
        print(json.dumps(server_state, indent=2))

        return server_state

    @property
    def xc_server_info(self) -> XcServerInfo:
        try:
            return self.settings["xcube_server_info"]
        except KeyError:
            return None, None, []

    @xc_server_info.setter
    def xc_server_info(self, value: XcServerInfo):
        self.settings["xcube_server_info"] = value

    @property
    def xc_server_output(self) -> XcServerOutput:
        try:
            return self.settings["xcube_server_output"]
        except KeyError:
            return None, None

    @xc_server_output.setter
    def xc_server_output(self, value: XcServerOutput):
        out, err = value
        if isinstance(out, bytes):
            out = out.decode('utf-8')
        if isinstance(err, bytes):
            err = err.decode('utf-8')
        self.settings["xcube_server_output"] = out, err

    def _start_server(self):
        process, _, _ = self.xc_server_info
        if process is not None and process.is_running():
            return

        if not server_config_file.exists():
            with server_config_file.open("w") as f:
                f.write(default_server_config)

        # TODO (forman): Get free port
        port = default_server_port

        cmdline = [
            sys.executable,
            "-m",
            "xcube.cli.main",
            "--logfile", f"{server_log_file}",
            "--loglevel", "DETAIL",
            "serve",
            "-v",
            "--config", f"{server_config_file}",
            "--port", f"{port}",
            "--update-after", "1",
        ]
        if is_jupyter_server_proxy_enabled():
            cmdline.extend(["--revprefix", f"/proxy/{port}"])

        self.log.info(f'Starting xcube Server: {cmdline}')
        try:
            process = psutil.Popen(cmdline,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
            self.xc_server_info = process, port, cmdline

            def communicate():
                self.xc_server_output = process.communicate()

            threading.Thread(target=communicate).start()

        except OSError as e:
            raise tornado.web.HTTPError(
                status_code=500,
                log_message=f'Starting xcube Server failed: {e}'
            ) from e

    def _stop_server(self):
        process, _, _ = self.xc_server_info
        if process is not None:
            process.kill()
