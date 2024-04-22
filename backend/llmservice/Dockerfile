FROM python:3.11-slim-bookworm

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN export CUDA_VISIBLE_DEVICES=1 \
    && apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install --no-cache-dir -r /code/requirements.txt

COPY . /code

CMD ["python", "consumer.py"]
