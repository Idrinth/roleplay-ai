FROM nvidia/cuda:12.9.1-base-ubuntu24.04

RUN apt update && apt install python3.12 python3.12-venv python3-pip -y
COPY Training/requirements.txt ./
RUN python3 -m venv ./.venv && .venv/bin/pip install --no-cache-dir -r requirements.txt
COPY Training/*.py ./training
COPY Training/training.json ./

ENTRYPOINT [".venv/bin/python3", "training"]