FROM python:3.9-slim as builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

ENV TZ=Europe/Moscow

CMD [ "python3", "-u", "main.py"]