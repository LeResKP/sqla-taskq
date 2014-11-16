from taskq import models
import transaction
from taskq.scripts import funcs


def add_task():
    with transaction.manager:
        models.Task.create(funcs.test_func1,
                           args=['hello'],
                           kw={'p': 'world'},
                           unique_key='hello')
        models.Task.create(funcs.test_func2,
                           args=['hello'],
                           kw={'p': 'world'},
                           unique_key='hello')


if __name__ == '__main__':
    add_task()
