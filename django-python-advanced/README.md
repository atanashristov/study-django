# [Master Django REST Framework with Docker, Dev to Production](../detailed-django-rest-api/)

Links:

- [Udemy course](https://www.udemy.com/course/django-python-advanced)

The course uses Django 3 and adds sections to upgrade to newer versions.

## Section 5: Project Setup

We use Docker together with Django.

- Define Dockerfile - contains all the OS level dependencies
- Define python dependency requirements
- Create Docker Compose configuration - how to run the images from Dockerfile
- Run all commands via Docker Compose
- Docker on GitHub actions - has rate limits
- Docker Hub - has rate limits
  - 100 pulls / 6h for unauthenticated users
  - 200 pulls / 6h for authenticated users
- GitHub actions as a shared service
  - 100 pulls / 6hr applied for all users
  - Go around it - AUthenticate with Docker Hub
    - Create account
    - Setup credentials
    - Login before running job

Create account at <https://hub.docker.com/>
Create account at <https://github.com/>
Create new public repository at GitHub with README and Python .gitignore <https://github.com/atanashristov/recipe-app-api>.

I added it as a submodule here:

```sh
git submodule add https://github.com/atanashristov/recipe-app-api
git submodule update --init --recursive
git submodule update --recursive --remote
```

On DockerHub navigate to Account - Account Settings - Personal Access Token.

Create an access token. For name use the name of the project "recipe-app-api". Make it with no expiration and "Read-only". Copy the personal access token.

To use the access token from your Docker CLI client run `docker login -u atanashristov`.
At the password prompt use your access token.

On GitHub go to the repo and add a secret. Click on Settings - Secrets and variables - Actions and click on "New Repository Secret"

Give it a name of "DOCKERHUB_USER". For value give it the name of the DockerHub user.

Add second repository secret. Name it "DOCKERHUB_TOKEN". For value paste the DockerHub access token.

### Docker and Django

Drawback: VSCode unable to access interpreter and debug.

Using Docker Compose:

- Run all commands through Docker Compose

```sh
docker-compose run --rm app sh -c "python manage.py collectstatic"
```

- `docker-compose` - runs Docker Compose command
- `run` - will start a specific container defined in config
- `--rm` - removes the container, this is recommended so we don't have a buildup of lingering containers
- `app` - the name of the service as defined in the compose config file
- `sh` - command that we run on the container. `sh -c` passes a shell command to the container
- Command to run on the container

Define a list ot python requirements in requirements.txt:

```sh
Django>=3.2.4,<3.3
djangorestframework>=3.12.4,<3.13
```

Create Dockerfile:

```sh
FROM python:3.9-alpine3.13
LABEL maintainer="hristov.app"

# See the output on the console without buffering
ENV PYTHONUNDUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

# Run as a single command to keep lightwait and not to create multiple layers
RUN python -m venv /py && \
  /py/bin/pip install --upgrade pip && \
  /py/bin/pip install -r /tmp/requirements.txt && \
  rm -rf /tmp && \
  adduser \
    --disabled-password \
    --no-create-home \
    django-user

ENV PATH="/py/bin:$PATH"

USER django-user
```

Create .dockerignore file - specify list of files to exclude from Docker context. We don;t want to copy these in the Docker container:

```sh
# Git
.git
.gitignore

# Docker
.docker

# Python
app/__pycache__/
app/*/__pycache__/
app/*/*/__pycache__/
app/*/*/*/__pycache__/
.env/
.venv/
venv/
```

Create ampty `app` subdirectory.

Test building our image: `docker build .` and see if any errors

Create `docker-compose.yaml` file:

```yaml
version: '3.9'

services:
  app:
    build:
      context: .
    ports:
      - '8000:8000'
    volumes:
      - ./app:/app
    command: >
      sh -c "python manage.py runserver 0.0.0.0:8000"
```

We map the local `./app` folder to the container's `/app`.
We want whatever content we have locally to have it in the container.
That way we sync automatically and we don;t need to rebuild.

The command we can override every time when run the `docker-compose`, but this here is the default.

Run the docker-compose: `docker-compose build`

Note: Since I am running Rancher Desktop, the compose command in the Docker CLI supports most of the docker-compose commands and flags.
It is expected to be a drop-in replacement for docker-compose.

```sh
docker compose up -d
docker compose down
docker compose build 
...
```

### Linting and Testing

Steps:

- Install `flake8` package
- Run it through Docker Compose

```sh
docker compose run --rm app sh -c "flake8"
```

If they are linting errors it will print in the console.
If they are multiple errors, the recommendation is to work these from bottom up.

For unit testing we are using te Django test suite:

- Setup tests per Django app
- Run the tests through Docker Compose

```sh
docker compose tun --rm app sh -c "python manage.py test"
```

Configure `flake8` tool.

Create `requirements.dev.txt` file:

```sh
flake8>=3.9.2,<3.10
```

We will add a separate build step for development, that's why we separate the requirements.

We add to docker-compose.yaml "DEV" argument:

```yaml
services:
  app:
    build:
      context: .
      args:
        - DEV=true
...
```

And we add to the "Dockerfile":

```sh
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

ARG DEV=false
```

When we use the Dockerfile through the `docker-compose.yaml` configuration we will set `DEV=true`.

When we run it thought other Docker Compose configuration it will be defaulted to false.

Then we add to run command in the Dockerfile the `if` statement below:

```sh
RUN python -m venv /py && \
  /py/bin/pip install --upgrade pip && \
  /py/bin/pip install -r /tmp/requirements.txt && \
  if [ $DEV = "true" ]; \
    then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
  fi && \
  ...
```

We add configuration for flake8. Mainly we want to exclude files that we don't need.

We add the file inside the `./app` directory `./app/.flake8`:

```ini
[flake8]
exclude =
  migrations,
  __pycache__,
  manage.py,
  settings.py
```

And now test the linter tool:

```sh
docker compose run --rm app sh -c "flake8"
```
