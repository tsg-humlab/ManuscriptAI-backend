#!/bin/sh

## Check that Postgres is running
#if [ "$DATABASE" = "postgres" ]
#then
#    echo "Waiting for Postgres..."
#
#    while ! nc -z $SQL_HOST $SQL_PORT; do
#      sleep 0.1
#    done
#
#    echo "PostgreSQL started"
#fi
#
## Check that Redis is running
#if ! [ -z $REDIS_HOST ]
#then
#  echo "Waiting for Redis..."
#
#  while ! nc -z $REDIS_HOST $REDIS_PORT; do
#    sleep 0.1
#  done
#
#  echo "Redis started"
#fi

exec "$@"
