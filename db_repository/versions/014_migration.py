from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
tags = Table('tags', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('tag_id', Integer),
    Column('body', String),
    Column('post_id', Integer),
    Column('tag_author', Integer),
)

tags = Table('tags', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('team_tag_id', Integer),
    Column('user_tag_id', Integer),
    Column('body', String(length=200)),
    Column('post_id', Integer),
    Column('tag_author', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['tags'].columns['tag_id'].drop()
    post_meta.tables['tags'].columns['team_tag_id'].create()
    post_meta.tables['tags'].columns['user_tag_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['tags'].columns['tag_id'].create()
    post_meta.tables['tags'].columns['team_tag_id'].drop()
    post_meta.tables['tags'].columns['user_tag_id'].drop()
