from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='sqla-taskq',
      version=version,
      description="Simple task queue executed by a daemon",
      long_description=open('README.rst').read().split('Build Status')[0],
      classifiers=[
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
      ],
      keywords='taskq, unix, sqlalchemy, task, queue',
      author='Aur\xc3\xa9lien Matouillot',
      author_email='a.matouillot@gmail.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'SQLAlchemy',
          'transaction',
          'python-daemon==1.6.1',
          'zope.sqlalchemy',
          'importlib',
          'supervisor',
      ],
      setup_requires=[
          'nose',
      ],
      test_suite='nose.collector',
      tests_require=[
          'mock',
          'coverage',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      sqla_taskq_daemon = sqla_taskq.run_daemon:main
      sqla_taskq_initializedb = sqla_taskq.scripts.initializedb:main
      """,
      )
