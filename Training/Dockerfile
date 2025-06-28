FROM nvidia/cuda:12.9.1-base-ubuntu24.04

RUN apt update && apt install python3.12 python3.12-venv python3-pip git cmake libcurl4-openssl-dev build-essential -y
WORKDIR /training
COPY Training/requirements.txt ./
RUN python3 -m venv ./.venv && .venv/bin/pip install --no-cache-dir -r requirements.txt
COPY Training/*.py ./training
RUN mkdir /training-data && mkdir /raw-data
COPY Training/data/*.json /raw-data/

ENTRYPOINT [".venv/bin/python3", "training"]