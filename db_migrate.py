#! /usr/bin/env python

#creates a migration by comparing structure for the db (app.db) against structure of our models (app/models.py) - Difference b/n two are recorded as migration script inside migration repository

#migration script knows how to apply or undo a migration, so it's always possible to upgrade or downgrade a database format

import imp
from migrate.versioning import api
from app import db
from settings import settings

mrepo = settings.sqlalchemy_migrations_repo
db_url = settings.database.url

migration = mrepo + '/versions/%03d_migration.py' % (api.db_version(db_url, mrepo) + 1)
tmp_module = imp.new_module('old_model')
old_model = api.create_model(db_url, mrepo)
exec old_model in tmp_module.__dict__
script = api.make_update_script_for_model(db_url, mrepo, tmp_module.meta, db.metadata)
open(migration, "wt").write(script)
api.upgrade(db_url, mrepo)
print 'New migration saved as ' + migration
print 'Current database version: ' + str(api.db_version(db_url, mrepo))
