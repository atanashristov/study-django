from .base import *
from .base import env

DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SERET_KEY', default='django-insecure-d44s&2pz5!im%j+oc)c+b3$!p-g5&p$b8hh=1#%b0l7fgciekr')


ALLOWED_HOSTS = [
    'localhost'
    '0.0.0.0',
    '127.0.0.1'
]
