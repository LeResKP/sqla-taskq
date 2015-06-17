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
    import taskq.models as taskqm

    settings = {
        'sqlalchemy.url': 'sqlite:///tmp/myproject.sqlite'
    }
    engine = engine_from_config(settings, 'sqlalchemy.')
    # You can set the engine for your project here

    # taskq should use the same engine
    taskqm.DBSession.configure(bind=engine)
    taskqm.Base.metadata.bind = engine


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
        export TASKQ_SQLALCHEMY_URL=sqlite:////tmp/taskq.db
        taskq_initializedb

        # Your can check you have created the database:
        ll /tmp/taskq.db


.. note:: if a database already exists for the given dialect, the database will not be erased, it will just add the new table.


Inserting a task
================


You just have to call `Task.create` with the function to call and optionally args and kwargs.

Here is an example:

.. code-block:: bash

    from taskq.models import Task
    args = [1, 2]
    kw = {'a': 1, 'b': 2}
    Task.create(mymodule.myfunction, args, kw)


Running the daemon
==================

Before running the daemon make sure the database is created. There is 3 ways to pass the DB dialect:

* Using the environment variable

.. code-block:: bash

    export TASKQ_SQLALCHEMY_URL=sqlite:////tmp/taskq.db
    taskq_daemon start

* Using the '-u' parameters

.. code-block:: bash

    taskq_daemon -u sqlite:////tmp/taskq.db start

* Using a config file

We suppose we have a file named /tmp/taskq.ini with this content

.. code-block:: ini

    [taskq]
    sqla_url = sqlite:////tmp/taskq.db

You can call the daemon like this

.. code-block:: bash

    taskq_daemon start -c /tmp/taskq.ini

    # Daemon status
    taskq_daemon status

    # Stop the daemon
    taskq_daemon stop

.. note:: If the daemon is running, passing parameters to the status or the stop function will have not effect.


Command line and file parameters
---------------------------------

.. note:: You can run taskq_daemon --help

``-u/--url`` <str>: the sqlalchemy url to use (like sqlite:////tmp/taskq.db)
Config file name: ``sqla_url``

``-t/--timeoout`` <int> (Default: 60s): The timeout in second the daemon wait before killing running task after a stop. No effect if ``-k`` is passed.
Config file name: ``timeout``

``-k/--kill``: kill the task when stopping. It will not wait for the end of the current task.
Config file name: ``kill``

``-c/--config-file`` <filename> : Pass a config file to the daemon


.. note:: The advantage of using config file is to be sure we always use the same conf and to be able to defined logging.


Supervisor
==========

taskq can be run with supervisor.

You can add this config to your supervisor config or create a new one like in `this example file <https://github.com/LeResKP/taskq/blob/develop/taskq/examples/supervisor.conf>`_.

.. code-block:: ini

    [program:taskq]
    command=python taskq/run_supervisor.py
    process_name=%(program_name)s-%(process_num)01d
    numprocs = 4



Demo
====

You have to clone the repository from github and execute the following command line:

.. code-block:: bash

    git clone https://github.com/LeResKP/taskq.git
    cd taskq
    mkvirtualenv taskq-env
    python setup.py develop
    taskq_initializedb
    python taskq/examples/add_tasks.py

Now we will just run the daemon to let it execute the tasks


.. code-block:: bash

    python taskq/run_daemon.py start

You should see the output on your terminal::

    started with pid XXX
    Process started
    test_func1 called
    test_func1 done
    test_func2 called
    test_func2 done

Now you can stop the daemon

.. code-block:: bash

    python taskq/run_daemon.py stop


Testing with supervisor
-----------------------

.. code-block:: bash

    python taskq/examples/add_tasks.py

    # Starting supervisor
    supervisord -c taskq/examples/supervisor.conf

    # Status
    supervisorctl -c taskq/examples/supervisor.conf status

    # Stop the process
    supervisorctl -c taskq/examples/supervisor.conf stop all

    # Kill supervisord
    killall supervisord

.. toctree::
   :maxdepth: 2
