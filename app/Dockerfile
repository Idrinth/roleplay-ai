FROM python:3.13

COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/*.pem ./app/
COPY app/*.schema.json ./app/
COPY app/rules.md ./app/
COPY app/*.py ./app/

CMD ["fastapi", "run", "app/main.py", "--port", "80"]
