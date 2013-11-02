#!flask/bin/python
from migrate.versioning import api
from settings import settings

mrepo = settings.sqlalchemy_migrations_repo
db_url = settings.database.url

api.upgrade(db_url, mrepo)
print 'Current database version: ' + str(api.db_version(db_url, mrepo))
