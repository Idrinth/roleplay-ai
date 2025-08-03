FROM python:3.13

ARG BEAM_TOKEN

WORKDIR /beam
RUN pip install beam-client
RUN beam configure default --token ${BEAM_TOKEN} || true

WORKDIR /beam/shared
COPY beam-llm-hosting/shared/*.py ./

WORKDIR /beam
COPY beam-llm-hosting/gamemaster/requirements.remote.txt ./
COPY beam-llm-hosting/gamemaster/main.py ./

RUN beam deploy main.py:answer

ENTRYPOINT ["echo", "ready"]
