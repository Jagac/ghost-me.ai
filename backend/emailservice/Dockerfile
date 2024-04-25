FROM python:3.10-slim

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt
COPY . /code

CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8000"]
# CMD [ "python", "main.py" ]