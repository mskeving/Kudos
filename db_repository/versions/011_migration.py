from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
teams = Table('teams', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('teamname', String(length=120)),
)

usersteams = Table('usersteams', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', Integer),
    Column('team_id', Integer),
)

users = Table('users', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nickname', String),
    Column('email', String),
    Column('about_me', String),
    Column('last_seen', Date),
    Column('firstname', String),
    Column('lastname', String),
    Column('phone', String),
    Column('team', String),
    Column('photo', String),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['teams'].create()
    post_meta.tables['usersteams'].create()
    pre_meta.tables['users'].columns['team'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['teams'].drop()
    post_meta.tables['usersteams'].drop()
    pre_meta.tables['users'].columns['team'].create()
