FROM python:3.13

ARG BEAM_TOKEN

WORKDIR /beam
RUN pip install beam-client
RUN beam configure default --token ${BEAM_TOKEN} || true

WORKDIR /beam/shared
COPY beam-llm-hosting/shared/*.py ./

WORKDIR /beam
COPY beam-llm-hosting/characterbuilder/requirements.remote.txt ./
COPY beam-llm-hosting/characterbuilder/main.py ./

RUN beam deploy main.py:answer

ENTRYPOINT ["python", "shared/shutdown.py", "--name=roleplay-ai-characterbuilder"]
