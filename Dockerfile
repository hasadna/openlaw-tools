FROM python:3.6-alpine

MAINTAINER Yehuda Deutsch <yeh@uda.co.il>

ENV PYTHONUNBUFFERED 1

RUN apk update && \
    apk add gcc musl-dev libffi-dev openssl-dev libmagic poppler-utils git perl perl-dev build-base && \
    pip install pipenv && \
    cpan install IPC::Run

RUN git clone https://github.com/hasadna/openlaw-bot.git /usr/local/lib/openlaw-bot
ENV OPENLAW_BOT_LIB /usr/local/lib/openlaw-bot

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --deploy --system

WORKDIR /app
ENV PYTHONPATH /app

COPY . /app

VOLUME ["/app/uploads"]
EXPOSE 8081

CMD ["python", "server.py"]
