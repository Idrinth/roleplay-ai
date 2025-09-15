FROM python:3.13

ARG BEAM_TOKEN

WORKDIR /training
COPY beam-llm-training/shared/*.txt ./
RUN mkdir /training/raw-data

RUN pip install --no-cache-dir -r requirements.txt
RUN beam configure default --token ${BEAM_TOKEN} || true

WORKDIR /training/shared
COPY beam-llm-training/shared/*.py ./

WORKDIR /training
COPY beam-llm-training/characterbuilder/__init__.py ./
COPY beam-llm-training/characterbuilder/main.py ./
COPY beam-llm-training/characterbuilder/data/*.yml ./raw-data/

ENTRYPOINT ["python", "main.py"]
