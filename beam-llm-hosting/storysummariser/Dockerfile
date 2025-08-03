FROM python:3.13

ARG BEAM_TOKEN

WORKDIR /beam
RUN pip install beam-client
RUN beam configure default --token ${BEAM_TOKEN} || true
COPY beam-llm-hosting/shared/*.py ./
COPY beam-llm-hosting/storysummariser/requirements.remote.txt ./
COPY beam-llm-hosting/storysummariser/main.py ./

RUN beam deploy main.py:answer

ENTRYPOINT ["echo", "ready"]
