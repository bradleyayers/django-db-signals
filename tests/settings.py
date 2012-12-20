from os.path import abspath, dirname, join

ROOT = dirname(abspath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(ROOT, 'default.sqlite3'),
    },
    'alternate': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(ROOT, 'alternative.sqlite3'),
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.admin',
    'django_db_signals',
    'tests.app',
]

SECRET_KEY = '1234567890'
