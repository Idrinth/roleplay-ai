FROM python:3.13

COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY resources/logo_secondary_in_white.png ./logo.png
COPY app/*.schema.json ./app/
COPY system-prompts/*.md ./
COPY app/*.py ./app/

RUN rm ./app/test_*.py

CMD ["fastapi", "run", "app/main.py", "--port", "80"]
