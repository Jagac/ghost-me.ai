FROM python:3.10-alpine

RUN apk add build-base
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --default-timeout=100 -r /code/requirements.txt
COPY . /code


CMD ["python", "main.py"]
