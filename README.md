# Manuscript AI

## Introduction

Manuscript AI consists of a frontend and a backend. Two implementations of the backend have been made: one based on Flask and one based on Django. It is the latter one, the django-based backend, on which this repository focuses. 

## Links

* [Project website](https://www.ru.nl/en/research/research-projects/manuscriptai)
* [Editor repository (with the earlier Flask backend)](https://github.com/tsg-humlab/ManuscriptAI-Editor) (fork of [TNO repo](https://github.com/ManuscriptAI/Editor))
* [New Django backend repository](https://github.com/tsg-humlab/ManuscriptAI-backend)

## People

* [Shari Boodts](mailto:shari.boodts@ru.nl) - RU (PI)
* [Giulia Biagioni](mailto:giulia.biagioni@tno.nl) - TNO
* [Ioannis Tolios](ioannis.tolios@tno.nl) - TNO (Developer)
* [Alex Wissink](mailto:alex.wissink@ru.nl) - RU (Research Assistent)
* Micha Hulsbosch - RU (developer)
* Erwin Komen - RU (developer)


## Description

Manuscript AI is a web application to enrich manuscript documents with metadata.

The front-end is made with [Vue](https://vuejs.org/) and the back-end with Django (originally Flask). With `docker compose` (which uses `docker-compose.yml`) two containers are created: *frontend* and *backend*. The *frontend* container also contains an Nginx server as reverse proxy that redirects all request for `/api/` to the backend.

> [!WARNING]
> "Use branch 'django-backend' of the forked repo"
>    We use branch `django-backend` of the TSG fork of the Editor repository to merge the changes from the upstream (=forked/original) repository and everything that is necessary to incorporate the Django backend. 
>    
>    To get changes from the upstream repository, go to [https://github.com/tsg-humlab/ManuscriptAI-Editor]() and click on `Sync fork`. Then do 
>
>    ```bash linenums="0"
>    git switch django-backend
>    git merge main
>    ```

## Instances


### Test

:octicons-globe-24: [test.manuscript-ai.rich.ru.nl](https://test.manuscript-ai.rich.ru.nl/)

:material-server: Lightning

:octicons-rel-file-path-24: `/var/www/manuscriptai-editor/repo` and `/var/www/manuscriptai-backend/repo`

In the first folder, there is a symlink to the second, `backend_django -> /var/www/manuscriptai-backend/repo/`, and `docker-compose.yml` is changed to

```yaml
services:
  backend:
    build: 
      context: ./backend_django
    command: gunicorn manuscriptai_ru_backend_v2.wsgi:application --bind 0.0.0.0:5001 --log-level debug --workers=${NUMBER_OF_WORKERS:-4} --timeout 900
    volumes:
      - static_volume:/home/app/web/staticfiles
      - tmp_volume:/home/app/web/tmp
      - writable_volume:/home/app/writable/   
    ports:
      - "5001:5001"
    env_file:
      - ./backend_django/.env
    networks:
      - app_network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - app_network
    restart: unless-stopped

networks:
  app_network:
    driver: bridge

volumes:
  static_volume:
  tmp_volume:
  writable_volume:
```

In the folder of the back-end there is a `.env` file that looks like this:

```bash
OPENAI_API_KEY=<an OpenAI key>
SECRET_KEY=<a properly generated Django secret key>
DEBUG=False
ALLOWED_HOSTS = test.manuscript-ai.rich.ru.nl,localhost
CSRF_TRUSTED_ORIGINS = https://test.manuscript-ai.rich.ru.nl
TIME_ZONE = CET
```

#### Deploying changes

*See also the info about using the `django-backend` branch from the forked repo.*

To get changes from either the front-end or the back-end repo, do the following:

1. Go to `/var/www/manuscriptai-editor/repo` and run `docker compose down` to stop the Docker containers.
2. Do `git pull` in either `/var/www/manuscriptai-editor/repo` or `/var/www/manuscriptai-backend/repo` or both.
3. In `/var/www/manuscriptai-editor/repo` run `docker compose build` and finally `docker compose up -d`

#### Running Django commands

You can run Django commands als follows:

```bash linenums="0"
docker compose backend ./manage.py collectstatic
```

#### Viewing logs

Logs can be viewed with `docker compose logs --follow backend` where '--follow' lets you views news log entries as they come in, and 'backend' may be replaced to view the logs of the front-end.

#### Connecting to the admin of the back-end

Because the back-end runs on port 5001, it cannot be reached directly from the internet. To reach it you need to establish an SSH tunnel with a so called *jump*. First make sure you have a user on the Lightning container for manuscriptai-test. Then, from a Linux shell you can do

```bash linenums="0"
ssh -L 5001:localhost:5001 -J <username-on-lightning>@lightning.science.ru.nl <username-on-manuscript-test>@10.208.155.225
```

This command connects `localhost:5001` on your computer to `localhost:5001` on 10.208.155.225 which can be reached if you first *jump* to `lightning.science.ru.nl`.

If the SSH tunnel is established, go to [http://localhost:5001/admin](http://localhost:5001/admin).


### Live

:octicons-globe-24: [manuscript-ai.rich.ru.nl](https://manuscript-ai.rich.ru.nl/)

The ip address of the manuscriptai container on Lightning: 10.208.155.23.

The live server is set up almost the same as the test server, except for the SECRET_KEY, ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS in the `.env` file of the back-end.
