FROM python:3.11-alpine

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app

CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8000"]