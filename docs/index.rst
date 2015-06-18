.. sqla-taskq documentation master file, created by
   sphinx-quickstart on Fri Jun 12 07:55:53 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


sqla-taskq
==========

`sqla-taskq` in an asynchronous task queue using sqlalchemy to store the task. It's minimalist but very useful when you don't want to put in place big system like celery. The supported back end are the same as sqlalchemy.


Engine settings
===============

.. code-block:: python

    from sqlalchemy import engine_from_config
    import sqla_taskq.models as sqla_taskqm

    settings = {
        'sqlalchemy.url': 'sqlite:///tmp/myproject.sqlite'
    }
    engine = engine_from_config(settings, 'sqlalchemy.')
    # You can set the engine for your project here

    # sqla-taskq should use the same engine
    sqla_taskqm.DBSession.configure(bind=engine)
    sqla_taskqm.Base.metadata.bind = engine


Creating DB table
=================

`sqla-taskq` needs only one table named `task`. There are 2 ways to create it:

* You can add this line to your python script which initializes your tables.

    .. code-block:: python

        # The engine should be the same as in your project
        models.Base.metadata.create_all(engine)

* You can call these commands

    .. code-block:: bash

        # Example with a sqlite dialect
        export SQLA_TASKQ_SQLALCHEMY_URL=sqlite:////tmp/sqla_taskq.db
        sqla_taskq_initializedb

        # Your can check you have created the database:
        ll /tmp/sqla_taskq.db


.. note:: if a database already exists for the given dialect, the database will not be erased, it will just add the new table.


Inserting a task
================


You just have to call `Task.create` with the function to call and optionally args and kwargs.

Here is an example:

.. code-block:: bash

    from sqla_taskq.models import Task
    args = [1, 2]
    kw = {'a': 1, 'b': 2}
    Task.create(mymodule.myfunction, args, kw)


Running the daemon
==================

Before running the daemon make sure the database is created. There is 3 ways to pass the DB dialect:

* Using the environment variable

.. code-block:: bash

    export SQLA_TASKQ_SQLALCHEMY_URL=sqlite:////tmp/sqla_taskq.db
    sqla_taskq_daemon start

* Using the '-u' parameters

.. code-block:: bash

    sqla_taskq_daemon -u sqlite:////tmp/sqla_taskq.db start

* Using a config file

We suppose we have a file named /tmp/sqla_taskq.ini with this content

.. code-block:: ini

    [sqla_taskq]
    sqla_url = sqlite:////tmp/sqla_taskq.db

You can call the daemon like this

.. code-block:: bash

    sqla_taskq_daemon start -c /tmp/sqla_taskq.ini

    # Daemon status
    sqla_taskq_daemon status

    # Stop the daemon
    sqla_taskq_daemon stop

.. note:: If the daemon is running, passing parameters to the status or the stop function will have not effect.


Command line and file parameters
---------------------------------

.. note:: You can run sqla_taskq_daemon --help

``-u/--url`` <str>: the sqlalchemy url to use (like sqlite:////tmp/sqla_taskq.db)
Config file name: ``sqla_url``

``-t/--timeoout`` <int> (Default: 60s): The timeout in second the daemon wait before killing running task after a stop. No effect if ``-k`` is passed.
Config file name: ``timeout``

``-k/--kill``: kill the task when stopping. It will not wait for the end of the current task.
Config file name: ``kill``

``-c/--config-file`` <filename> : Pass a config file to the daemon


.. note:: The advantage of using config file is to be sure we always use the same conf and to be able to defined logging.


Supervisor
==========

sqla-taskq can be run with supervisor.

You can add this config to your supervisor config or create a new one like in `this example file <https://github.com/LeResKP/sqla-taskq/blob/develop/sqla-taskq/examples/supervisor.conf>`_.

.. code-block:: ini

    [program:sqla_taskq]
    command=python sqla_taskq/run_supervisor.py
    process_name=%(program_name)s-%(process_num)01d
    numprocs = 4



Demo
====

You have to clone the repository from github and execute the following command line:

.. code-block:: bash

    git clone https://github.com/LeResKP/sqla-taskq.git
    cd sqla_taskq
    mkvirtualenv sqla_taskq-env
    python setup.py develop
    sqla_taskq_initializedb
    python sqla_taskq/examples/add_tasks.py

Now we will just run the daemon to let it execute the tasks


.. code-block:: bash

    python sqla_taskq/run_daemon.py start

You should see the output on your terminal::

    started with pid XXX
    Process started
    test_func1 called
    test_func1 done
    test_func2 called
    test_func2 done

Now you can stop the daemon

.. code-block:: bash

    python sqla_taskq/run_daemon.py stop


Testing with supervisor
-----------------------

.. code-block:: bash

    python sqla_taskq/examples/add_tasks.py

    # Starting supervisor
    supervisord -c sqla_taskq/examples/supervisor.conf

    # Status
    supervisorctl -c sqla_taskq/examples/supervisor.conf status

    # Stop the process
    supervisorctl -c sqla_taskq/examples/supervisor.conf stop all

    # Kill supervisord
    killall supervisord

.. toctree::
   :maxdepth: 2
