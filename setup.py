from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='taskq',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
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
          'python-daemon',
          'zope.sqlalchemy',
      ],
      test_suite='nose.collector',
      tests_require=[
          'nose',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      taskq_daemon = taskq.run:main
      """,
      )
