#! /usr/bin/env python

from migrate.versioning import api
from settings import settings
from app import db
import os.path

db.create_all()

mrepo = settings.sqlalchemy_migrations_repo
db_url = settings.database.url

if not os.path.exists(mrepo):
    api.create(mrepo, 'database repository')
    api.version_control(db_url, mrepo)
else:
    api.version_control(db_url, mrepo, api.version(mrepo))
