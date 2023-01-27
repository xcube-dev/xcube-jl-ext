import json
import subprocess
from typing import Any, Dict

import jupyter_server.base.handlers
import psutil

from ..config import default_server_config
from ..config import default_server_port
from ..config import is_jupyter_server_proxy_enabled
from ..config import server_config_file
from ..config import server_info_file
from ..config import server_log_file


# noinspection PyAbstractClass
class ServerHandler(jupyter_server.base.handlers.APIHandler):

    # @tornado.web.authenticated
    def get(self):
        server_info = self._load_server_info()
        server_state = self._get_server_state(server_info)
        self.finish(server_state)

    # @tornado.web.authenticated
    def put(self):
        server_info = self._load_server_info()
        server_state = self._get_server_state(server_info)
        if server_state.get("status") != "running":
            server_info = self._start_server()
            server_state = self._get_server_state(server_info)
        self.finish(server_state)

    # @tornado.web.authenticated
    def delete(self):
        server_info = self._load_server_info()
        self._stop_server(server_info)
        self.finish({})

    def _start_server(self):
        if not server_config_file.exists():
            with server_config_file.open("w") as f:
                f.write(default_server_config)

        port = default_server_port

        cmd = [
            "xcube",
            "--logfile", f"{server_log_file}",
            "--loglevel", "DETAIL",
            "serve",
            "-v",
            "--config", f"{server_config_file}",
            "--port", f"{port}",
            "--update-after", "1",
        ]
        if is_jupyter_server_proxy_enabled():
            cmd.extend(["--revprefix", f"/proxy/{port}"])

        self.log.info(f'Starting xcube Server: {cmd}')
        try:
            process = subprocess.Popen(cmd)
        except OSError as e:
            message = f'Starting xcube Server failed: {e}'
            self.log.error(message, error=e)
            raise RuntimeError(message) from e

        if process.returncode is not None:
            message = f'Starting xcube Server failed: ' \
                      f' exit with return code {process.returncode}'
            self.log.error(message)
            raise RuntimeError(message)

        return self._dump_server_info(process.pid, port)

    @staticmethod
    def _stop_server(server_info: Dict[str, Any]):
        pid = server_info.get("pid")
        if isinstance(pid, int):
            try:
                process = psutil.Process(pid)
                process.terminate()
            except psutil.NoSuchProcess:
                pass
        server_info_file.unlink()

    @staticmethod
    def _dump_server_info(pid: int, port: int) -> Dict[str, Any]:
        server_info = {
            "pid": pid,
            "port": port,
        }
        if not server_info_file.parent.exists():
            server_info_file.parent.mkdir(parents=True, exist_ok=True)
        with server_info_file.open("w") as fp:
            json.dump(server_info, fp)
        return server_info

    @staticmethod
    def _load_server_info() -> Dict[str, Any]:
        if server_info_file.exists():
            with server_info_file.open() as fp:
                return json.load(fp)
        return {}

    @staticmethod
    def _get_server_state(server_info: Dict[str, Any]) -> Dict[str, Any]:
        pid = server_info.get("pid")
        if isinstance(pid, int):
            try:
                process = psutil.Process(pid)
                return {
                    "status": process.status(),
                    "name": process.name(),
                    "username": process.username(),
                    "cmdline": process.cmdline(),
                    **server_info
                }
            except psutil.NoSuchProcess:
                pass
        return {}
