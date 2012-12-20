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


Installation
============

1. Install from PyPI: ``pip install django-db-signals``.
2. Add ``'django_db_signals'`` to ``INSTALLED_APPS``.
3. Enable the signals by adding to your ``models.py``::

    import django_db_signals
    django_db_signals.enable()


Example
=======

Let's assume you've installed django-db-signals, and now you'd like to log a
message each time the database is rolled back::

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
such, attempting to import individual signals will fail::

    >>> import django_db_signals
    >>> django_db_signals.enable()
    >>> # GOOD
    ...
    >>> from django.db import signals
    >>> signals.pre_commit
    <django.dispatch.dispatcher.Signal object at 0x1089c8b90>
    >>> # BAD
    ...
    >>> from django.db.signals import pre_commit
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    ImportError: No module named signals


``pre_…`` vs ``post_…`` signals
-------------------------------

A distinction is made between ``pre_…`` and ``post_…`` signals. ``pre_…``
signals are sent using the normal ``.send(…)`` method, allowing receivers to
raise exceptions and abort the pending operation.

For ``post_…`` signals, the operation has already occurred. As such, it's more
important to ensure all receivers are called (rather than propagate
exceptions).

For this reason, ``post_…`` signals are sent via ``.send_robust(…)``. Any
exceptions raised in receivers are logged (via a ``django.db.signals`` logger)
and then ignored.

This means that unlike ``pre_…`` receivers, exceptions raised from ``post_…``
receivers will *not* interrupt execution flow of the application.


signal senders
--------------

For all database signals, the sender of the signal is Django's database
connection wrapper.


Troubleshooting
===============

    "I can import ``django.db.signals``, but when I try to access a signal I get
    an ``AttributeError`` exception."

You need to enable the signals via ``django_db_signals.enable()``
