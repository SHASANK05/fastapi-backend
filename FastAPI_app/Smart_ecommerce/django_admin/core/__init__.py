import pymysql

pymysql.install_as_MySQLdb()

# Bypass Django 6.1+ strict MySQL 8.4 requirement for local MySQL 8.0
from django.db.backends.base.base import BaseDatabaseWrapper

BaseDatabaseWrapper.check_database_version_supported = lambda self: None