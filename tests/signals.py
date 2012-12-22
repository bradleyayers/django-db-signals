# coding: utf-8
from __future__ import unicode_literals
from .app.models import Person
from attest import assert_hook, Tests
from contextlib import contextmanager
from django.db import connections, DEFAULT_DB_ALIAS, signals, transaction
from django_attest import TransactionTestContext


suite = Tests()
suite.context(TransactionTestContext(multi_db=True))
conn = lambda alias: connections[DEFAULT_DB_ALIAS if alias is None else alias]


# -- helpers-------------------------------------------------------------------


@contextmanager
def connect(signal, handler):
    """
    Connect and disconnect a signal receiver using a context manager::

        def handler(sender, **kwargs):
            ...

        with connect(pre_commit, handler):
            ...

    """
    signal.connect(handler)
    try:
        yield
    finally:
        signal.disconnect(handler)


@suite.context
def log():
    """
    Setup handlers for each transaction signal to log a unique string to a
    list, then pass the list to the test.

    This makes it easy to verify which signals were called and in what order.

    - *pre_transaction_management* -- ``(``
    - *post_transaction_management* -- ``)``
    - *pre_commit* -- ``…✔``
    - *post_commit* -- ``✔…``
    - *pre_rollback* -- ``…✘``
    - *post_rollback* -- ``✘…``
    """
    log = []
    senders = []

    def make_handler(token):
        # make a handler that writes a specific token to *msgs*, and the sender
        # to *senders*
        def handler(sender, **kwargs):
            log.append(token)
            senders.append(sender)
        return handler

    with connect(signals.pre_commit,                  make_handler('…✔')), \
         connect(signals.post_commit,                 make_handler('✔…')), \
         connect(signals.pre_rollback,                make_handler('…✘')), \
         connect(signals.post_rollback,               make_handler('✘…')), \
         connect(signals.pre_transaction_management,  make_handler('(')), \
         connect(signals.post_transaction_management, make_handler(')')):
         yield (log, senders)


# -- tests --------------------------------------------------------------------


def commit_on_success(client, log, senders, using):
    with transaction.commit_on_success(using=using):
        Person.objects.db_manager(using).create(name="foo")
    assert log == ['(', '…✔', '✔…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return commit_on_success(client, log, senders, using)


def leave_transaction_management_not_dirty(client, log, senders, using):
    with transaction.commit_on_success(using=using):
        pass
    assert log == ['(', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return leave_transaction_management_not_dirty(client, log, senders, using)


def commit_on_success_rollback(client, log, senders, using):
    try:
        with transaction.commit_on_success(using=using):
            Person.objects.db_manager(using).create(name="foo")
            raise IndexError
    except IndexError:
        pass
    assert log == ['(', '…✘', '✘…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return commit_on_success_rollback(client, log, senders, using)


def commit_manually_rollback(client, log, senders, using):
    try:
        with transaction.commit_manually(using=using):
            Person.objects.db_manager(using).create(name="foo")
    except transaction.TransactionManagementError:
        log.append('!')
    assert log == ['(', '…✘', '✘…', ')', '!']
    assert senders == [conn(using)] * (len(log) - 1)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return commit_manually_rollback(client, log, senders, using)


def commit_manually_commit(client, log, senders, using):
    with transaction.commit_manually(using=using):
        Person.objects.db_manager(using).create(name="foo")
        transaction.commit(using=using)
    assert log == ['(', '…✔', '✔…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return commit_manually_commit(client, log, senders, using)


def robust_post_rollback(client, log, senders, using):
    class Foo(Exception):
        pass

    def buggy(sender, **kwargs):
        raise Exception

    with connect(signals.post_rollback, buggy):
        with transaction.commit_manually(using=using):
            Person.objects.db_manager(using).create(name="foo")
            transaction.rollback(using=using)

    assert log == ['(', '…✘', '✘…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return robust_post_rollback(client, log, senders, using)


def robust_post_commit(client, log, senders, using):
    class Foo(Exception):
        pass

    def buggy(sender, **kwargs):
        raise Exception

    with connect(signals.post_commit, buggy):
        with transaction.commit_on_success(using=using):
            Person.objects.db_manager(using).create(name="foo")

    assert log == ['(', '…✔', '✔…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return robust_post_commit(client, log, senders, using)


def exit_managed_with_pending_commit(client, log, senders, using):
    with transaction.commit_manually(using=using):
        Person.objects.db_manager(using).create(name="foo")
        transaction.managed(False, using=using)

    assert Person.objects.using(using).get(name="foo")
    assert log == ['(', '…✔', '✔…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return exit_managed_with_pending_commit(client, log, senders, using)


def rollback_unless_managed__in_managed(client, log, senders, using):
    with transaction.commit_on_success(using=using):
        cursor = conn(using).cursor()
        cursor.execute('INSERT INTO app_person (name) VALUES (%s)', ['foo'])
        transaction.rollback_unless_managed(using=using)
    assert Person.objects.using(using).get(name="foo")
    assert log == ['(', '…✔', '✔…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return rollback_unless_managed__in_managed(client, log, senders, using)


def rollback_unless_managed__in_auto(client, log, senders, using):
    with transaction.autocommit(using=using):
        cursor = conn(using).cursor()
        cursor.execute('INSERT INTO app_person (name) VALUES (%s)', ['foo'])
        transaction.rollback_unless_managed(using=using)
    assert Person.objects.using(using).filter(name="foo").count() == 0
    assert log == ['(', '…✘', '✘…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return rollback_unless_managed__in_auto(client, log, senders, using)


def commit_unless_managed__in_managed(client, log, senders, using):
    # Being inside a managed block, commit_unless_managed will be a noop, and
    # the `transaction.rollback()` will rollback the INSERT.
    with transaction.commit_manually(using=using):
        cursor = conn(using).cursor()
        cursor.execute('INSERT INTO app_person (name) VALUES (%s)', ['foo'])
        transaction.commit_unless_managed(using=using)
        transaction.rollback(using=using)
    assert Person.objects.using(using).filter(name="foo").count() == 0
    assert log == ['(', '…✘', '✘…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return commit_unless_managed__in_managed(client, log, senders, using)


def commit_unless_managed__in_auto(client, log, senders, using):
    # Being inside an auto block, commit_unless_managed will commit, and
    # the `transaction.rollback()` will rollback nothing.
    with transaction.autocommit(using=using):
        cursor = conn(using).cursor()
        cursor.execute('INSERT INTO app_person (name) VALUES (%s)', ['foo'])
        transaction.commit_unless_managed(using=using)
        transaction.rollback(using=using)
    assert Person.objects.using(using).get(name="foo")
    assert log == ['(', '…✔', '✔…', '…✘', '✘…', ')']
    assert senders == [conn(using)] * len(log)

for alias in (None, 'default', 'alternate'):
    @suite.test
    def parameterized(client, log, senders, using=alias):
        return commit_unless_managed__in_auto(client, log, senders, using)
