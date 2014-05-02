from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    Boolean,
    PickleType,
    UnicodeText,
    create_engine,
)

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension
import transaction
import inspect
import importlib


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base(DBSession)
engine = create_engine('sqlite:///taskq.db', echo=False)
DBSession.configure(bind=engine)
Base.metadata.bind = engine
Base.query = DBSession.query_property()

import logging
log = logging.getLogger(__name__)


TASK_STATUS_WAITING = 'waiting'
TASK_STATUS_IN_PROGRESS = 'inprogress'
TASK_STATUS_FINISHED = 'finished'


class Task(Base):
    _func_params = [
        ('_instance', None),
        ('_func_name', None),
        ('_args', []),
        ('_kw', {}),
    ]

    __tablename__ = 'task'

    idtask = Column(Integer, nullable=False, autoincrement=True,
                    primary_key=True)
    func = Column(PickleType, nullable=False)
    description = Column(UnicodeText, nullable=False)
    result = Column(UnicodeText, nullable=True)
    status = Column(String, nullable=False, default=TASK_STATUS_WAITING)

    def __init__(self):
        for p, d in self._func_params:
            setattr(self, p, None)

    @orm.reconstructor
    def init_on_load(self):
        self.load_func()

    @classmethod
    def create(cls, func, args=None, kw=None, description=None):
        with transaction.manager:
            task = cls()
            if inspect.ismethod(func):
                task._instance = func.__self__
                task._func_name = func.__name__
            elif inspect.isfunction(func) or inspect.isbuiltin(func):
                task._func_name = '%s.%s' % (func.__module__, func.__name__)
            else:
                task._func_name = func

            task.description = description
            if description is None:
                if func.__doc__:
                    task.description = func.__doc__.splitlines()[0]

            if task.description is None:
                # TODO: create a nice fallback
                task.description = ('%s' % func.__name__)

            task._args = args
            task._kw = kw

            task.func = task.dump_func()
            task.status = TASK_STATUS_WAITING
            DBSession.add(task)
            log.debug('Task created for %s' % func)
        return task

    def dump_func(self):
        """Create dict to store in the DB as pickle
        """
        data = {}
        for param, d in self._func_params:
            data[param] = getattr(self, param)
        return data

    def load_func(self):
        """Set the parameter to self from the dict stored in the DB
        """
        for param, d in self._func_params:
            v = self.func[param]
            if v is None:
                v = d
            setattr(self, param, v)

    def get_func(self):
        """Get the function to be able to call it!
        """
        if self._instance:
            return getattr(self._instance, self._func_name)

        module_name, attribute = self._func_name.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, attribute)

    def perform(self):
        """Call the function with its parameters
        """
        func = self.get_func()
        self._args = self._args or []
        self._kw = self._kw or {}
        self.result = func(*self._args, **self._kw)
        return self.result
