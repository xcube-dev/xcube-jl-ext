import importlib.metadata
import json
import sys
from pathlib import Path

import tornado
import tornado.escape
import tornado.httpclient
import tornado.httputil
import tornado.web
from jupyter_server.base.handlers import APIHandler

from ..config import data_path
from ..config import has_proxy_key
from ..config import lab_info_path
from ..config import lab_url_key


# noinspection PyAbstractClass
class LabInfoHandler(APIHandler):
    # @tornado.web.authenticated
    def get(self):
        self._assert_lab_info_file()
        with lab_info_path.open(mode="r") as f:
            lab_info = json.load(f)
        self.finish(lab_info)

    # @tornado.web.authenticated
    def put(self):
        if not data_path.is_dir():
            data_path.mkdir()
        lab_info = tornado.escape.json_decode(self.request.body)
        self._validate_lab_info(lab_info)
        lab_info[has_proxy_key] = self._has_jupyter_server_proxy()
        with lab_info_path.open(mode="w") as f:
            json.dump(lab_info, f, indent=2)
        self.finish(lab_info)

    # @tornado.web.authenticated
    # noinspection PyMethodMayBeStatic
    def delete(self):
        self._assert_lab_info_file()
        lab_info_path.unlink()
        self.finish({})

    @staticmethod
    def _assert_lab_info_file():
        if not lab_info_path.is_file():
            raise tornado.web.HTTPError(
                404, reason="Lab info not found"
            )

    @staticmethod
    def _validate_lab_info(lab_info):
        lab_url = None
        if isinstance(lab_info, dict):
            lab_url = lab_info.get(lab_url_key)
        if not isinstance(lab_url, str) or lab_url == "":
            raise tornado.web.HTTPError(
                400, reason="Missing or invalid Lab info in request body"
            )

    @staticmethod
    def _has_jupyter_server_proxy():
        # Is it installed?
        try:
            importlib.metadata.version("jupyter-server-proxy")
        except importlib.metadata.PackageNotFoundError:
            return False
        # Is it installed?
        frontend_dir = Path(sys.prefix,
                            "share", "jupyter", "labextensions",
                            "@jupyterlab", "server-proxy")
        if not frontend_dir.is_dir():
            return False

        # Ok,jupyter-server-proxy is installed.
        # Now check whether it is disabled.
        is_disabled = False

        # File page_config.json will only exist,
        # if @jupyterlab/server-proxy has been disabled once.
        page_config_file = Path(sys.prefix,
                                "etc", "jupyter", "labconfig",
                                "page_config.json")
        if page_config_file.is_file():
            with page_config_file.open() as fp:
                page_config = json.load(fp)
            try:
                is_disabled = page_config.get("disabledExtensions", {}).get(
                    "@jupyterlab/server-proxy", False)
            except AttributeError:
                pass

        return is_disabled
