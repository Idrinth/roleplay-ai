FROM python:3.13

COPY App/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY App/*.min.js ./app/
COPY App/*.schema.json ./app/
COPY App/*.yaml ./app/
COPY App/*.py ./app/
COPY App/index.html ./app/

CMD ["fastapi", "run", "app/main.py", "--port", "80"]