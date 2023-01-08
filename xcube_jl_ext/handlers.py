import json
from pathlib import Path

import tornado
import tornado.escape
import tornado.httpclient
import tornado.httputil
import tornado.web
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join

config_path = Path("~").expanduser() / ".xcube"
lab_info_path = config_path / "lab-info.json"
lab_url_key = "lab_url"


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
        if not config_path.is_dir():
            config_path.mkdir()
        lab_info = tornado.escape.json_decode(self.request.body)
        self._validate_lab_info(lab_info)
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


# noinspection PyAbstractClass
class ServerHandler(APIHandler):
    # @tornado.web.authenticated
    def get(self):
        # TODO
        pass

    # @tornado.web.authenticated
    def put(self):
        # TODO
        pass

    # @tornado.web.authenticated
    def delete(self):
        # TODO
        pass


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    web_app.add_handlers(host_pattern, [
        (url_path_join(base_url, "xcube", "labinfo"), LabInfoHandler),
        (url_path_join(base_url, "xcube", "server"), ServerHandler),
    ])
