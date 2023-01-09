import json

import tornado
import tornado.escape
import tornado.httpclient
import tornado.httputil
import tornado.web
from jupyter_server.base.handlers import APIHandler

from ..config import data_path
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
