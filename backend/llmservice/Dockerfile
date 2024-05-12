FROM python:3.11-slim-bookworm

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --timeout 1000 torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --timeout 1000 -r /app/requirements.txt

COPY . /app
CMD ["python", "main.py"]
