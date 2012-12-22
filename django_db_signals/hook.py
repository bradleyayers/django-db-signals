# coding: utf-8
from __future__ import with_statement
from contextlib import contextmanager
import django.db
from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.dispatch import Signal
from django.utils import importlib
from functools import wraps
import logging


logger = logging.getLogger('django.db.signals')
IS_DJANGO_12 = (1, 2, 0) <= django.VERSION < (1, 3, 0)


class DatabaseSignals(object):
    """A container for the database signals."""

    def __init__(self):
        self.pre_commit = Signal()
        self.post_commit = Signal()
        self.pre_rollback = Signal()
        self.post_rollback = Signal()
        self.pre_transaction_management = Signal()
        self.post_transaction_management = Signal()


# Add django.db.transaction.signals API
django.db.signals = signals = DatabaseSignals()
del DatabaseSignals


# Get a connection object that corresponds to a given alias
conn = lambda alias: connections[DEFAULT_DB_ALIAS if alias is None else alias]


def send_robust_and_log_errors(signal_name, **kwargs):
    signal = getattr(signals, signal_name)
    responses = signal.send_robust(**kwargs)
    for receiver, response in responses:
        if isinstance(response, Exception):
            logger.error('%s receiver "%r" failed: %r' %
                         (signal_name, receiver, response))


def patch(target_path):
    """
    A decorator that patches a function by using the decorated function as
    a contextmanager. The function must return a generator that yields once.
    """
    def decorator(wrapper):
        module_path, target_name = target_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        target = getattr(module, target_name)

        manager = contextmanager(wrapper)

        @wraps(target)
        def wrapped(*args, **kwargs):
            with manager(*args, **kwargs):
                target(*args, **kwargs)

        setattr(module, target_name, wrapped)
    return decorator


@patch("django.db.transaction.commit")
def commit(using=None):
    # This will raise an exception if the commit fails. django.db.transaction
    # decorators catch this and call rollback(), but the middleware doesn't.
    connection = conn(using)
    signals.pre_commit.send(sender=connection)
    yield
    send_robust_and_log_errors("post_commit", sender=connection)


@patch("django.db.transaction.commit_unless_managed")
def commit_unless_managed(using=None):
    if not transaction.is_managed(using=using):
        connection = conn(using)
        signals.pre_commit.send(sender=connection)
        yield
        send_robust_and_log_errors("post_commit", sender=connection)
    else:
        yield


@patch("django.db.transaction.enter_transaction_management")
def enter_transaction_management(managed=True, using=None):
    signals.pre_transaction_management.send(sender=conn(using))
    yield


# commit() isn't called at the end of a transaction management block if there
# were no changes. This function is always called so the signal is always sent.
@patch("django.db.transaction.leave_transaction_management")
def leave_transaction_management(using=None):
    connection = conn(using)
    # Django 1.2's implementation of leave_transaction_management() calls
    # the patched rollback() function, however in later versions the unpatched
    # DatabaseWrapper.rollback() is used. Thus, in 1.2 we don't want to send
    # [pre/post]_rollback signals, otherwise they'll be sent twice.
    #
    # If the transaction is dirty, it is rolled back and an exception is
    # raised. We need to send the rollback signal before that happens.
    is_dirty = transaction.is_dirty(using=using)
    if is_dirty and not IS_DJANGO_12:
        signals.pre_rollback.send(sender=connection)
    try:
        yield
    finally:
        if is_dirty and not IS_DJANGO_12:
            send_robust_and_log_errors("post_rollback", sender=connection)
        send_robust_and_log_errors("post_transaction_management", sender=connection)


@patch("django.db.transaction.managed")
def managed(flag=True, using=None):
    # Turning transaction management off (flag=False) causes the current
    # transaction to be committed if it's dirty. We must send the signal after
    # the actual commit.
    # https://github.com/django/django/blob/master/django/db/transaction.py#L100
    should_commit = not flag and transaction.is_dirty(using=using)
    connection = conn(using)
    if should_commit:
        signals.pre_commit.send(sender=connection)
    yield
    if should_commit:
        send_robust_and_log_errors("post_commit", sender=connection)


@patch("django.db.transaction.rollback")
def rollback(using=None):
    connection = conn(using)
    signals.pre_rollback.send(sender=connection)
    yield
    # The rollback has happened and can't be undone. Notify *all* receivers,
    # then log exceptions
    send_robust_and_log_errors("post_rollback", sender=connection)


@patch("django.db.transaction.rollback_unless_managed")
def rollback_unless_managed(using=None):
    if not transaction.is_managed(using=using):
        connection = conn(using)
        signals.pre_rollback.send(sender=connection)
        yield
        send_robust_and_log_errors("post_rollback", sender=connection)
    else:
        yield
