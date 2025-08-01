FROM python:3.11

ARG BEAM_TOKEN

WORKDIR /training
COPY training/requirements.txt ./
RUN mkdir /training/raw-data

RUN pip install --no-cache-dir -r requirements.txt
RUN beam configure default --token ${BEAM_TOKEN} || true

COPY training/requirements.remote.txt ./
COPY training/__init__.py ./
COPY training/data/*.yml ./raw-data/
COPY training/main.py ./

ENTRYPOINT ["python", "main.py"]
