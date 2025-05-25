# [Build a Backend REST API with Python & Django - Advanced](../django-python-advanced)

Links:

- [Udemy course](https://www.udemy.com/course/detailed-django-rest-api/)
- [Code](./authors-haven-api/)
- [Copy of the original code](./authors-haven-api-original/)
- [Original course repository](https://github.com/API-Imperfect/authors-haven-api-live)

Run the project:

```sh
cd authors-haven-api
python -m venv env
source env/Scripts/activate # env/Scripts/activate  (Windows)
pip3 install --upgrade pip # or: python -m pip install --upgrade pip
pip3 install -r requirements/local.txt
pip3 list # optionally list and confirm all installed required packages
```

The project has virtual environment created with: `python -m venv env`.

The Django project was initiated with: `django-admin startproject authors_api .`.

Apps are created with running _manage.py_ like that: `python manage.py startapp users` and moved to _core_apps_.

The `.gitignore` was created with: `npx gitignore python`.

To run the project, first export environment variable "DATABASE_URL".

Example with Postgres on Windows with PoserShell, database name is "authorshaven-dev-1" in this example:

```sh
$Env:DATABASE_URL = "postgres://usernamehere:passwordhere@127.0.0.1:5432/authorshaven-dev-1"

echo $Env:DATABASE_URL

Get-ChildItem Env:
Get-ChildItem Env:DATABASE_URL
```

Then run:

```sh
python manage.py runserver
```
