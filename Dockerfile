FROM python:3.8-alpine

ADD . /api
WORKDIR /api

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN pip install -r requirements.txt
RUN python setup.py develop
#ENV DATABASE_URI postgresql://postgres:postgres@postgres-monolith:5432/postgres
#ENV FLASK_RUN_HOST 0.0.0.0
#ENV FLASK_APP app.py
#ENV PYTHONPATH ./

EXPOSE 5000

#CMD flask run