from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
users = Table('users', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nickname', String),
    Column('email', String),
    Column('role', SmallInteger),
    Column('about_me', String),
    Column('last_seen', Date),
)

users = Table('users', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('firstname', String(length=64)),
    Column('lastname', String(length=64)),
    Column('nickname', String(length=64)),
    Column('email', String(length=120)),
    Column('phone', String(length=25)),
    Column('team', String(length=120)),
    Column('about_me', String(length=140)),
    Column('last_seen', Date),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['users'].columns['role'].drop()
    post_meta.tables['users'].columns['firstname'].create()
    post_meta.tables['users'].columns['lastname'].create()
    post_meta.tables['users'].columns['phone'].create()
    post_meta.tables['users'].columns['team'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['users'].columns['role'].create()
    post_meta.tables['users'].columns['firstname'].drop()
    post_meta.tables['users'].columns['lastname'].drop()
    post_meta.tables['users'].columns['phone'].drop()
    post_meta.tables['users'].columns['team'].drop()
