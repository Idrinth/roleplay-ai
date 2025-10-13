FROM python:3.14

COPY github-cache/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY github-cache/*.py ./app/

CMD ["fastapi", "run", "app/main.py", "--port", "80"]
