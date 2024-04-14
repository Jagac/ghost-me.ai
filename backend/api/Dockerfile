FROM python:3.11-alpine


WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --default-timeout=100 -r /code/requirements.txt
COPY . /code


CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
