#!flask/bin/python
from migrate.versioning import api
from settings import settings

mrepo = settings.sqlalchemy_migrations_repo
db_url = settings.database.url

v = api.db_version(db_url, mrepo)
api.downgrade(db_url, mrepo, v - 1)
print 'Current database version: ' + str(api.db_version(db_url, mrepo))
