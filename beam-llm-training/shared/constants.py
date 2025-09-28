from beam import Image

GLOBAL_BZ = 32
DEVICES = [0]
MAX_SEQUENCE_LENGTH = 131072
BZ=1
IMAGE = Image(python_version="python3.12", python_packages="requirements.remote.txt", env_vars="HF_HUB_ENABLE_HF_TRANSFER=1").add_commands(["apt-get update", "apt-get install cmake g++ curl libcurl4-openssl-dev -y"])
