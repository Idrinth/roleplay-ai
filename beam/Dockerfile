FROM python:3.13

ARG BEAM_TOKEN

WORKDIR /beam
RUN pip install beam-client
RUN beam configure default --token ${BEAM_TOKEN} || true
COPY beam/requirements.remote.txt ./
COPY beam/gmai.py ./

RUN beam deploy gmai.py:answer

RUN curl -X POST 'https://gamemaster-ai-9e68ad7.app.beam.cloud/warmup' \
    -H "Authorization: Bearer ${BEAM_TOKEN}"

ENTRYPOINT ["echo", "ready"]
