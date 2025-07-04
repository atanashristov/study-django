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
We want whatever content we have locally to have it in the container, and vice versa.
That way we sync automatically and we don't need to rebuild.

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
docker compose run --rm app sh -c "python manage.py test"
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

Create Django project.
We create a new project on the Docker image, as Django is already installed in it.
The "." at the end says : create app in the current directory, instead creating a subdirectory "app/app":

```sh
docker compose run --rm app sh -c "django-admin startproject app ."
```

You can see it adds `manage.py` under `./app`.

Run the project (the dev server) with Docker Compose:

```sh
docker compose up
```

We can now access the project on the web by browsing to <http://127.0.0.1:8000/>.

To stop the server, press Ctrl+C.

## Section 6: GitHub automated actions

Common uses:

- Deployment (nit )
- Code linting
- Unit tests

We add on-push triggers to run unit tests.

Pricing:

- Charged per minute
- Every account gets 2,000 free minutes

Configuring GitHub actions:

- Add `.github/workflows/checks.yml` file
- Set trigger and steps to lint and unit tests
- We pull images from DockerHub - it has rate limits
  - Anonymous: 100/6h (identifies by IP)
  - Authenticated: 200/6h
- GitHub Actions uses shared IP addresses
  - Limit applied to all users
- We will authenticate GitHub Actions with Docker Hub
  - 200 pulls per 6h all to ourselves

How to authenticate with Docker Hub?

- Register account on <https://hub.docker.com/>
- Use `docker login` during our job
- Add secrets to GitHub project.
  - These are encrypted
  - Only decrypted during actions execution

## Section 7: TDD in Django

Django has built in "Django test framework":

- Based on the `unittest` library
- Django adds
  - Test client - dummy web browser
  - Simulate authentication
  - Temporary database
- Django REST Framework adds features
  - API test client

Where do you put tests?

- Placeholder `tests.py` added to each app
- Or, create `tests/` subdirectory to split tests up
- Keep in mind:
  - Only use `tests.py` or `tests/` directory (not both)
  - Test modules must start with `test_`
  - Test directories must contain `__init__.py`

Test Database:

- Test code that uses the DB (reads, writes)
  - Separate than the real DB
- Specific database for tests
  - Django creates automatically
  - Runs a test and cleans the data
  - Runs the next test and cleans the data
  - ... etc.
    - You can override, so you have consistent data for all tests

Test classes:

- `SimpleTestCase`
  - No Db integration
  - Useful for code w/o database
- `TestCase`
  - Most common
  - Can read and write to DB

Add module `calc.py` with method `add()` - just so we have some code to test.

Add `tests.py` - see inside the unit tests for the `add()` method.

Run the tests: `docker compose run --rm app sh -c "python manage.py test"`.

We run a service `app` and shell command on it.

### Mocking

How to mock code?

- Use `unittest.mock`
  - `MagicMock/Mock` - Replace real objects
  - `patch` - Overrides code for tests

### Testing APIs

Django REST Framework `API Client`:

- Based on the Django's `TestClient`
- Make requests
- Check results
- Override authentication - test the behavior of the API assuming you are authenticated

### Common testing issues

Tests not running - it says you ran less tests that you actually have.

Possible reason is, you are missing the `__init__.py` file in the `tests/` dir.

Another possibility is wrong indentation in the test cases.

Common issue is seeing `ImportError` when running tests.

## Section 8: Configure Database

Will be using PostgreSQL and Docker Compose

We will have persistent volumes, so that we can reuse.

Volumes:

- Persistent data
- Maps directory in container to local machine

Changes in `docker-compose.yaml`:

- Define volume for Postgres data
- Define `db` service that pulls Postgres docker image
- It accesses the volume
- Define initial environment variables
  - Will create database, user and password for the user - this is initial setup for development
  - These will only be used on our local machine
- Change the `app` service to connect to the `db`
  - also to depend on it, so that `db` starts first, then `app`

Test the changes:

```sh
docker compose up -d
```

### Connect the Django app to the DB

All settings are defined in `settings.py` file.

We set environment variables and read these in `settings.py`.

We need the package `Psycopg2` package for Django to connect to Postgres.

Options to install `Psycopg2` are:

- Install `psycopg-binary`
  - OK for development
  - Not good for production (not optimized binary)
- Install `psycopg2`
  - Compiles from source to the specific OS
  - Downside: we have to have some dependencies to compile and install
  - Easy to install with Docker since we know and reuse the same image and OS!

List of package dependencies:

- C compiler
- python3-dev
- libpq-dev

Their equivalent in Alpine:

- postgresql-client
- build-base
- postgresql-dev
- musl-dev

Docker best practices:

- Cleanup build dependencies
  - Clean up these ^ dependencies when we build

Change the `Dockerfile`, see added apk commands to build the dependencies and clean up temporary file.
We also change the `requirements.txt` adding `psycopg2`.

Stop Docker Compose, Build and Run again:

```sh
docker compose down
docker compose build
docker compose up -d
```

In the `settings.py` define the default database set up with environment variables.

### Fixing DB racing conditions

Problems with Docker Compose:

- Using `depends_on` ensures the service starts
  - Does not ensure the application (Postgresql) is running yet
    - Can be a problem when starting the Django app
    - The DB may not be ready to accept connections
    - Can take longer for Postgres to start than teh Django app to start

Solution:

- Make Django "wait for db"
  - Checking for the availability of the database
  - Continue execution once the db is ready
- Create custom Django "wait_for_db" command for this

### We create new `core` app

```sh
docker compose run --rm app sh -c "python manage.py startapp core"
```

Remove `tests.py` and `views.py` files as we won't need those.

Create directory `tests` and `__init__.py` file in it.

Add the core app to the `app/settings.py` in `INSTALLED_APPS`

Write `wait_for_db` command as `app\core\management\commands\wait_for_db.py`.
Because of the directory names, Django will allow using that command in `python manage.py`.

And the unit tests are added here: `app\core\tests\test_commands.py`.

Mocking setup means: First 2 calls return the DB server is not started yet,
next 3 calls says the DB accepts connections, but is not ready (not yet operational),
then finally returns OK.

```py
    def test_wait_for_db_delay(self, patched_check):
        """Test waiting for database when getting OperationalError."""
        patched_check.side_effect = [Psycopg2Error] * 2 + \
            [OperationalError] * 3 + [True]
```

The patch is applied from the inside out - in that order:

```py
@patch('core.management.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    """Test commands."""

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
...
```

Run the unit tests and the flake linter:

```sh
docker compose run --rm app sh -c "python manage.py test && flake8"
```

This is how we can execute a command and thereof test it:

```sh
docker compose run --rm app sh -c "python manage.py wait_for_db"

[+] Creating 1/1
 ✔ Container recipe-app-api-db-1  Running                                                                                                                                             0.0s
Waiting for database...
Database available!
```

### Section 8. Chapter 42: Database Migrations

To create migrations run:

```sh
python manage.py makemigrations
```

To apply the migrations run:

```sh
python manage.py migrate
```

Best to run it every time after start the application - after waiting for DB.

### Section 8. Chapter 43: Update Docker Compose and CI/CD

We change the command in `docker-compose.yaml` for the "app":

```sh
      sh -c "python manage.py wait_for_db &&
             python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
```

Then we test with:

```sh
docker compose down
docker compose up
```

Then we change the "Test" step in the `.github/checks.yaml`:

```yaml
      - name: Test
        run: |
          docker compose run --rm app sh -c "python manage.py wait_for_db" &&
          docker compose run --rm app sh -c "python manage.py test"
```

## Section 9: Create User Model

### Section 9. Chapter 45: The Django user model

The default user model has some issues:

- Uses "username" instead of "email" for login
- Not easy to customize

So we create custom user model for new projects, so it is easier to customize.

We create a model class:

- Create model
  - Base from `AbstractBaseUser` and `PermissionsMixin`
- Create custom manager
  - Used for _CLI integration_
- Set `AUTH_USER_MODEL` in _settings.py_
- Create and run migrations for your project

The `AbstractBaseUser`:

- Provides features for authentication
- Doesn't include fields

The `PermissionsMixin`:

- Supports the Django permission system
- Includes _fields_ and _methods_
- Can be used from Django Admin

Since we already created _migrations_ we will have to clear those.
When working with custom user model it is recommended to create the model before running migrations.

### Section 9. Chapter 46: Design custom user model

User model manager:

- Used to manage objects from our custom user model
- Custom logic for creating objects
  - Hash password
- Used by Django CLI

`BaseUserManager` comes from Django:

- Base class for managing users
- Useful helper methods
  - `normalize_email`: for storing emails consistently
- Methods we'll define
  - `create_user`: called when creating user
  - `create_superuser`: used by the CLI to create a superuser (admin)

### Section 9. Chapter 47: Add user model tests

Create test file in `app/core/tests/test_models.py`.

Note: in VS Code we open "Settings" and from Text Editor - Files check the box for "Trim Trailing Space"

### Section 9. Chapter 48: Implement user model

Define user model class in `app/core/models.py`.

Add the model to `app/app/settings.py`:

```py
AUTH_USER_MODEL = 'core.User'
```

Then we can make migrations to our project:

```sh
docker compose run --rm app sh -c "python manage.py makemigrations"
[+] Creating 1/1
 ✔ Container recipe-app-api-db-1  Running                                                                                                                                  0.0s
Migrations for 'core':
  core/migrations/0001_initial.py
    - Create model User
```

Apply the migration to the docker compose:

```sh
docker compose run --rm app sh -c "python manage.py wait_for_db && python manage.py migrate"

[+] Creating 1/1
 ✔ Container recipe-app-api-db-1  Running                                                                                                                                                                                       0.0s
Waiting for database...
Database available!
Traceback (most recent call last):
  File "/app/manage.py", line 22, in <module>
    main()
  File "/app/manage.py", line 18, in main
    execute_from_command_line(sys.argv)
  File "/py/lib/python3.9/site-packages/django/core/management/__init__.py", line 419, in execute_from_command_line
    utility.execute()
  File "/py/lib/python3.9/site-packages/django/core/management/__init__.py", line 413, in execute
    self.fetch_command(subcommand).run_from_argv(self.argv)
  File "/py/lib/python3.9/site-packages/django/core/management/base.py", line 354, in run_from_argv
    self.execute(*args, **cmd_options)
  File "/py/lib/python3.9/site-packages/django/core/management/base.py", line 398, in execute
    output = self.handle(*args, **options)
  File "/py/lib/python3.9/site-packages/django/core/management/base.py", line 89, in wrapped
    res = handle_func(*args, **kwargs)
  File "/py/lib/python3.9/site-packages/django/core/management/commands/migrate.py", line 95, in handle
    executor.loader.check_consistent_history(connection)
  File "/py/lib/python3.9/site-packages/django/db/migrations/loader.py", line 306, in check_consistent_history
    raise InconsistentMigrationHistory(
django.db.migrations.exceptions.InconsistentMigrationHistory: Migration admin.0001_initial is applied before its dependency core.0001_initial on database 'default'.
```

OOPS! In this case we will have to clear the existing data, as we already pre-applied migrations.

Check for the database volume:

```sh
docker volume ls
DRIVER    VOLUME NAME
...
local     recipe-app-api_dev-db-data
```

, and then stop Docker Compose remove the volume:

```sh
docker compose down
docker volume rm recipe-app-api_dev-db-data
```

Then run the migrations again:

```sh
docker compose run --rm app sh -c "python manage.py wait_for_db && python manage.py migrate"
[+] Creating 3/3
 ✔ Network recipe-app-api_default       Created                                                                                                                                                                                 0.1s
 ✔ Volume "recipe-app-api_dev-db-data"  Created                                                                                                                                                                                 0.0s
 ✔ Container recipe-app-api-db-1        Created                                                                                                                                                                                 0.1s
[+] Running 1/1
 ✔ Container recipe-app-api-db-1  Started                                                                                                                                                                                       0.2s
Waiting for database...
Database unavailable, waiting 1 second...
Database unavailable, waiting 1 second...
Database available!
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, core, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying core.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying sessions.0001_initial... OK
```

Now we can run our test to verify the migration and creating a user:

```sh
docker compose run --rm app sh -c "python manage.py test"
```

### Section 9. Chapter 49: Normalize email address

Added tests to "test_models.py" and call to normalize the email in "models.py".

### Section 9. Chapter 50: Require email

Added tests to "test_models.py" and check for email in "models.py".

### Section 9. Chapter 51: Add superuser support

Added tests to "test_models.py" and "create_superuser" method in "models.py".

### Section 9. Chapter 52: Test the user model

If we run `docker compose up -d` it will not apply migrations as we did not change the model.

Browse to <http://localhost:8000/admin> and you should get the admin site.

In order to login, we have to create credentials. In the terminal run "createsuperuser" command to set your admin password:

```sh
 recipe-app-api  docker compose up -d
[+] Running 2/2
 ✔ Container recipe-app-api-db-1
 ✔ Container recipe-app-api-app-1

 recipe-app-api  docker compose run --rm app sh -c "python manage.py createsuperuser"
[+] Creating 1/1
 ✔ Container recipe-app-api-db-1
Email: admin@example.com
Password:
```

And then you can login to the admin portal.
