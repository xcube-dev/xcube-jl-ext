import json
import subprocess

import psutil
from jupyter_server.base.handlers import APIHandler

from ..config import default_server_config
from ..config import server_config_file
from ..config import server_log_file
from ..config import server_state_file

PORT = 8092


# noinspection PyAbstractClass
class ServerHandler(APIHandler):

    # @tornado.web.authenticated
    def get(self):
        server_state = self._load_server_state()
        pid = server_state.get("pid")
        if isinstance(pid, int):
            server_state = self._get_server_state(server_state,
                                                  psutil.Process(pid))
        self.finish(server_state)

    # @tornado.web.authenticated
    # noinspection PyAttributeOutsideInit
    def put(self):
        server_state = self._load_server_state()
        pid = server_state.get("pid")
        if isinstance(pid, int):
            process = psutil.Process(pid)
            if process.status() == "running":
                server_state = self._get_server_state(server_state, process)
                self.finish(server_state)
                return

        if not server_config_file.exists():
            with server_config_file.open("w") as f:
                f.write(default_server_config)
        port = PORT
        cmd = [
            "xcube",
            "--logfile", f"{server_log_file}",
            "--loglevel", "DETAIL",
            "serve",
            "-v",
            "--port", f"{port}",
            "--config", f"{server_config_file}"
        ]
        process = subprocess.Popen(cmd)
        server_state = self._dump_server_state(process.pid, port)
        server_state = self._get_server_state(server_state,
                                              psutil.Process(process.pid))
        self.finish(server_state)

    # @tornado.web.authenticated
    def delete(self):
        server_state = self._load_server_state()
        pid = server_state.get("pid")
        if isinstance(pid, int):
            process = psutil.Process(pid)
            process.terminate()
        server_state_file.unlink()
        self.finish({})

    @staticmethod
    def _dump_server_state(pid: int, port: int):
        server_state = {
            "pid": pid,
            "port": port,
        }
        with server_state_file.open("w") as fp:
            json.dump(server_state, fp)
        return server_state

    @staticmethod
    def _load_server_state():
        if server_state_file.exists():
            with server_state_file.open() as fp:
                return json.load(fp)
        return {}

    @staticmethod
    def _get_server_state(server_state, process):
        server_state = {
            "status": process.status(),
            "name": process.name(),
            "username": process.username(),
            **server_state
        }
        return server_state
