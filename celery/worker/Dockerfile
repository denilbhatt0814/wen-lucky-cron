FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false\
    && rm -rf /var/lib/apt/lists/*

# installing dependencies
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# copying scripts to container
COPY ./celery/worker/start.sh /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

WORKDIR /app
COPY . .

ENTRYPOINT [ "/start-celeryworker" ]