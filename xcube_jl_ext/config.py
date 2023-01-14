import importlib.metadata
from pathlib import Path

import jupyter_core.paths

data_path = Path("~").expanduser() / ".xcube"
lab_info_path = data_path / "lab-info.json"
lab_url_key = "lab_url"
has_proxy_key = "has_proxy"

server_info_file = data_path / "server-info.json"

server_log_file = data_path / "server-log.txt"

server_config_file = Path(".") / "xcube-server.yaml"

default_server_port = 9192

default_server_config = """
# xcube Server configuration file

DataStores:
  - Identifier: root
    StoreId: file
    StoreParams:
      root: .    

  #- Identifier: my-s3-bucket
  #  StoreId: s3
  #  StoreParams:
  #    root:  my-s3-bucket
  #    storage_options:
  #      anon: False
  #      key: my_aws_access_key_id
  #      secret: my_aws_secret_access_key    

"""


def is_jupyter_server_proxy_enabled() -> bool:
    """Check if the Jupyter server extension "jupyter-server-proxy"
     is installed and enabled."""

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
