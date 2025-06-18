FROM python

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./

CMD ["python", "main.py"]