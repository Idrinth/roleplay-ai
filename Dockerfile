FROM python:3.13

ADD app/requirements.txt ./

RUN pip install -r requirements.txt
