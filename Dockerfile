FROM python:3.6-alpine

MAINTAINER Yehuda Deutsch <yeh@uda.co.il>

ENV PYTHONUNBUFFERED 1

RUN apk update && apk add gcc musl-dev libffi-dev openssl-dev && pip install pipenv
# apt-get install build-essential libpoppler-cpp-dev pkg-config python-dev

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --deploy --system

WORKDIR /app
ENV PYTHONPATH=/app

COPY . /app

CMD ["python", "server.py"]
