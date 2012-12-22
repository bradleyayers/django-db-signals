=================
django-db-signals
=================

This app adds a set of signals to some of Django's database operations:

- ``django.db.signals.pre_commit``
- ``django.db.signals.post_commit``
- ``django.db.signals.pre_rollback``
- ``django.db.signals.post_rollback``
- ``django.db.signals.pre_transaction_management``
- ``django.db.signals.post_transaction_management``


Requirements
============

- Python 2.6/2.7/3.2/3.3 (3.x requires Django >=1.5)
- Django 1.2/1.3/1.4/1.5


Installation
============

1. Install from PyPI: ``pip install django-db-signals``.
2. Add ``'django_db_signals'`` to ``INSTALLED_APPS``.
3. Enable the signals by adding to your ``models.py``:

   .. code-block:: python

       import django_db_signals
       django_db_signals.enable()


Example
=======

Let's assume you've installed django-db-signals, and now you'd like to log a
message each time the database is rolled back:

.. code-block:: python

    from django.db import signals
    from django.dispatch import receiver
    import logging

    logger = logging.getLogger(__name__)

    @reciever(signals.post_rollback)
    def log_rollbacks(sender, **kwargs):
        # sender is a DatabaseWrapper object
        logger.info("A rollback occurred on database %s" %
                    sender.alias)


Design
======

In the same way that Django settings are available via ``django.conf.settings``
attributes, signals are available via ``django.db.signals`` attributes. As
such, attempting to import individual signals will fail:

.. code-block:: python

    >>> import django_db_signals
    >>> django_db_signals.enable()

    >>> from django.db import signals  # GOOD
    >>> signals.pre_commit
    <django.dispatch.dispatcher.Signal object at 0x1089c8b90>

    >>> from django.db.signals import pre_commit  # BAD
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    ImportError: No module named signals


``pre_…`` vs ``post_…`` signals
-------------------------------

``pre_…`` signals are sent *before* an operation occurs. The signals are sent
via ``.send(…)``. Exceptions raised in receivers are propagated to the
application. This can be exploited to cancel the operation (e.g. to block a
commit).

``post_…`` signals are sent *after* an operation, and as such can't offer the
same *cancel the pending operation* behaviour. The signal is sent via
``.send_robust(…)`` to ensure all receivers are called. Any exceptions raised
are logged, but are not propagated to the application.


Logging
-------

A logger named ``django.db.signals`` is used to log all exceptions raised in
``post_…`` receivers.


Signal senders
--------------

For all database signals, the sender of the signal is Django's database
connection wrapper.


Troubleshooting
===============

    "I can import ``django.db.signals``, but when I try to access a signal I get
    an ``AttributeError`` exception."

You need to enable the signals via ``django_db_signals.enable()``
