import importlib.metadata
import json
import os
import os.path
import sys
from pathlib import Path
from typing import Iterator

import tornado
import tornado.escape
import tornado.httpclient
import tornado.httputil
import tornado.web
import jupyter_server.base.handlers
import jupyter_core.paths

from ..config import data_path
from ..config import has_proxy_key
from ..config import lab_info_path
from ..config import lab_url_key


# noinspection PyAbstractClass
class LabInfoHandler(jupyter_server.base.handlers.APIHandler):
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
        lab_info[has_proxy_key] = has_proxy = _has_jupyter_server_proxy()
        self.log.info(f"lab_info: {lab_info}")
        with lab_info_path.open(mode="w") as fp:
            json.dump(lab_info, fp)
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


def _has_jupyter_server_proxy():
    # Is it installed?
    try:
        importlib.metadata.version("jupyter-server-proxy")
    except importlib.metadata.PackageNotFoundError:
        return False
    # Is it installed?
    is_installed = False
    for labext_dir in jupyter_core.paths.jupyter_path("labextensions",
                                                      "@jupyterlab",
                                                      "server-proxy"):
        if Path(labext_dir).is_dir():
            is_installed = True
            break
    if not is_installed:
        return False

    # Now check whether it is disabled.
    is_disabled = False
    for config_dir in jupyter_core.paths.jupyter_config_path():
        page_config_file = Path(config_dir) / "labconfig" / "page_config.json"
        # File page_config.json will only exist,
        # if @jupyterlab/server-proxy has been disabled once.
        if page_config_file.is_file():
            with page_config_file.open() as fp:
                page_config = json.load(fp)
            try:
                is_disabled = page_config.get("disabledExtensions", {}) \
                    .get("@jupyterlab/server-proxy", False)
                break
            except AttributeError:
                pass

    return not is_disabled


def _get_jupyter_config_dirs() -> Iterator[str]:
    """Get all possible Jupyter Server configuration paths. See
    https://docs.jupyter.org/en/latest/use/jupyter-directories.html#configuration-files
    """
    jupyter_config_dir = os.environ.get("JUPYTER_CONFIG_DIR")
    if jupyter_config_dir is not None:
        yield jupyter_config_dir

    jupyter_config_path = os.environ.get("JUPYTER_CONFIG_PATH")
    if jupyter_config_path is not None:
        yield from jupyter_config_path.split(os.path.pathsep)

    yield f"{sys.prefix}/etc/jupyter"

    if sys.platform == "win32":
        yield f"{os.environ.get('PROGRAMDATA')}/jupyter"
    else:
        yield "/usr/local/etc/jupyter"
        yield "/etc/jupyter"


def _get_jupyter_data_dirs() -> Iterator[str]:
    """Get all possible Jupyter Server data paths. See
    https://docs.jupyter.org/en/latest/use/jupyter-directories.html#data-files
    """
    jupyter_path = os.environ.get("JUPYTER_PATH")
    if jupyter_path is not None:
        # Directories given in JUPYTER_PATH are searched
        # before other locations.
        yield from jupyter_path.split(os.path.pathsep)

    jupyter_data_dir = os.environ.get("JUPYTER_DATA_DIR")
    if jupyter_data_dir is None:
        if sys.platform == "win32":
            jupyter_data_dir = f"{os.environ.get('APPDATA')}/jupyter"
        elif sys.platform == "darwin":
            jupyter_data_dir = os.path.expanduser("~/Library/Jupyter")
        else:
            jupyter_data_dir = os.path.expanduser("~/.local/share/jupyter")

    yield jupyter_data_dir
    yield f"{sys.prefix}/share/jupyter"

    if sys.platform == "win32":
        yield f"{os.environ.get('PROGRAMDATA')}/jupyter"
    else:
        yield "/usr/local/share/jupyter"
        yield "/usr/share/jupyter"
