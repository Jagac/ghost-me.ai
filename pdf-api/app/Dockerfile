# 
FROM python:3.10-slim

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --default-timeout=100 -r /code/requirements.txt
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.3.1/en_core_web_sm-2.3.1.tar.gz
RUN python3 -m spacy download en_core_web_sm
RUN python -m nltk.downloader stopwords
# 
COPY . /code

# 

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
