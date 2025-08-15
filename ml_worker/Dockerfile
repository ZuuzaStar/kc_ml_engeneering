FROM python:3.12-slim

WORKDIR /app

COPY ml_worker/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && pip install -r /app/requirements.txt

CMD ["python", "main.py"]