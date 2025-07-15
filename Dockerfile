###########
# BUILDER #
###########

# pull official base image
FROM python:3.12-slim as builder

# set work directory
WORKDIR /usr/src/django_app/

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update -y && apt-get upgrade -y &&\
    apt-get install -y --no-install-recommends gcc git

# install python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/django_app/wheels -r requirements.txt

#########
# FINAL #
#########

# pull official base image
FROM python:3.12-slim

# install dependencies
RUN apt-get update -y && apt-get upgrade -y && apt-get install -y --no-install-recommends netcat-traditional
COPY --from=builder /usr/src/django_app/wheels /wheels
COPY --from=builder /usr/src/django_app/requirements.txt .
#RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

# create the app user
RUN addgroup --system app && adduser --system --group --home /home/app app

# change to the app user
USER app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
RUN mkdir $APP_HOME/tmp
RUN mkdir -p $HOME/writable/database
WORKDIR $APP_HOME

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/entrypoint.sh
RUN chmod +x  $APP_HOME/entrypoint.sh

# copy project
COPY . $APP_HOME

# DiskCache workaround
RUN mkdir -p .cache
USER root
RUN chown -R app:app .cache
USER app

# run entrypoint.sh
ENTRYPOINT ["/home/app/web/entrypoint.sh"]
