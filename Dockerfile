FROM python:3.13

ADD App/requirements.txt ./

RUN pip install -r requirements.txt