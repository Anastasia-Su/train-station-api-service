
# Train Station API

API service for train station management, written on DRF.

## Installing / Getting started

Install Postgres and create db.

```shell
git clone https://github.com/Anastasia-Su/train-station-api-service.git
cd train-station-api-service
python -m venv venv
venv\Scripts\activate (on Windows)
source venv/bin/activate (on macOS)
pip install -r requirements.txt

set SECRET_KEY=<your secret key>
set POSTGRES_HOST=<your host name>
set POSTGRES_DB=<your database>
set POSTGRES_USER=<your usernane>
set POSTGRES_PASSWORD=<your password>

python manage.py migrate
python manage.py loaddata station_service_db_data.json (if you need sample data)
python manage.py runserver

```

## Run with Docker

Docker should be installed.

```shell
docker-compose build
docker-compose up
```

## Getting access

* Create user via /api/user/register
* Get access token via /api/user/token

## Features

* JWT authentication
* Admin panel: /admin/
* Documentation: api/doc/swagger/ and api/doc/redoc/
* Managing tickets and orders
* Creating trains, routes and journeys
* Adding images to trains
* Filtering trains and journeys

## Links

- DockerHub: https://hub.docker.com/repository/docker/anasu888/train-station-api-service-app/general
