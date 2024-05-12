FROM python:3.11-alpine

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --default-timeout=100 -r /app/requirements.txt
COPY . /app


CMD ["python", "main.py"]
