FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --default-timeout=100 -r /code/requirements.txt

RUN mkdir /code/model

RUN wget -O /code/model/llama-2-7b-chat.ggmlv3.q8_0.bin https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/raw/main/llama-2-7b-chat.ggmlv3.q8_0.bin

COPY . /code

CMD ["python", "consumer.py"]
