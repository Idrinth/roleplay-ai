FROM python:3.13

COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/*.schema.json ./app/
COPY app/rules.md ./app/
COPY app/*.py ./app/

RUN rm ./app/test_*.py

CMD ["fastapi", "run", "app/main.py", "--port", "80"]
