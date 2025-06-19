FROM python

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./app/
COPY index.html ./app/

CMD ["fastapi", "run", "app/main.py", "--port", "80"]