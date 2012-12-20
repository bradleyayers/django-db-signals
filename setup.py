# coding=utf-8
"""
Monkey-patch signals into ``django.db.transaction.signals.*``.

The following signals are defined and behave according to the description:

pre_commit
----------

Sent *prior* to the transaction being committed. Exceptions raised in handlers
will prevent the transaction from being committed, and will bubble up to the
application.


post_commit
-----------

Sent *after* the transaction is committed. The signal is sent via
`~Signal.send_robust`, meaning all handlers are executed. Exceptions raised in
handlers are logged but will not bubble up to the application.

This is done because there's nothing useful that allowing the exception to
bubble up will achieve. It's more important to execute all the handlers. Even
if you assume there is something useful in raising the exception, if two
handlers raise an exception, which one should be raised? Instead, both are
logged and not raised.


pre_rollback
------------

Sent *prior* to the transaction being rolled-back. Exceptions raised in
handlers will prevent the transaction from being rolled-back, and will bubble
up to the application.


post_rollback
-------------

Sent *after* the transaction as been rolled-back. The signal is sent via
`~Signal.send_robust`, meaning all handlers are executed. Exceptions raised in
handlers are logged but will not bubble up to the application.

A detailed rational for the exception smothering is in `post_commit`.


pre_transaction_management
--------------------------

Send *before* the ???


post_transaction_management
---------------------------

Send *after* leaving transaction management. This signal isn't sent if a
``TransactionManagementError`` is raised.


.. code-block:: python

    import djcelery_transactions.transaction_signals


    def _post_commit(**kwargs):
        print "The transaction has been committed!"


    django.db.transaction.signals.post_commit.connect(_post_commit)

This code was inspired by Grégoire Cachet's implementation of similar
functionality, which can be found on GitHub: https://gist.github.com/247844

.. warning::

    This module must be imported before you attempt to use the signals.
"""
from setuptools import setup


setup(
    name="django-db-signals",
    version="0.1.0",
    description="Django database transaction signals (pre/post commit/rollback).",
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
