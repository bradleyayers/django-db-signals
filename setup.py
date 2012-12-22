# coding=utf-8
from setuptools import setup


setup(
    name="django-db-signals",
    version="0.1.0",
    description="Django database signals (pre/post commit/rollback).",
    long_description=__doc__,
    author="Bradley Ayers",
    author_email="bradley.ayers@gmail.com",
    url="https://github.com/bradleyayers/django-db-signals",
    license="Simplified BSD",
    packages=["django_db_signals"],
    install_requires=["Django >=1.4"],
    classifiers=[
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        "Topic :: Database",
    ],
)
