FROM python:3.13

ARG BEAM_TOKEN

WORKDIR /beam
RUN pip install beam-client
RUN beam configure default --token ${BEAM_TOKEN} || true
COPY beam/requirements.remote.txt ./
COPY beam/gmai.py ./

ENTRYPOINT ["beam", "deploy", "gmai.py:answer"]
