from pathlib import Path

data_path = Path("~").expanduser() / ".xcube"
lab_info_path = data_path / "lab-info.json"
lab_url_key = "lab_url"

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