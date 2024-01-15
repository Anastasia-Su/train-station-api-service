FROM python:3.11.7-slim
LABEL maintainer="anastasia.su.po@gmail.com"
ENV PYTHONUNBUFFERED 1

WORKDIR app/
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install --no-cache-dir psycopg2-binary
RUN apt-get update && apt-get install -y ca-certificates

COPY . .

RUN mkdir -p /vol/web/media

RUN adduser --disabled-password --no-create-home django-user
RUN chown -R django-user:django-user /vol/
RUN chmod -R 755 /vol/web/

USER django-user
