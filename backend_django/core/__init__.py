import pymysql
from django.db.backends.base.base import BaseDatabaseWrapper

# 1. Register PyMySQL as MySQLdb
pymysql.install_as_MySQLdb()

# 2. Bypass strict MySQL 8.4 check in Django 6.1 for MySQL 8.0.x
BaseDatabaseWrapper.check_database_version_supported = lambda self: None