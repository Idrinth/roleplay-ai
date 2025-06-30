FROM nvidia/cuda:12.9.1-base-ubuntu24.04

RUN apt update && apt install python3.12 python3.12-venv python3-pip git cmake libcurl4-openssl-dev build-essential -y

WORKDIR /training
COPY Training/requirements.txt ./
RUN python3 -m venv ./.venv && .venv/bin/pip install --no-cache-dir -r requirements.txt
RUN mkdir /raw-data

WORKDIR /ollama
RUN git clone https://github.com/ggml-org/llama.cpp.git .
RUN python3 -m venv ./.venv && .venv/bin/pip install --no-cache-dir -r requirements.txt

WORKDIR /training
COPY Training/config.json ./
COPY Training/*.py ./training
COPY Training/data/*.json /raw-data/

ENTRYPOINT [".venv/bin/python3", "training"]