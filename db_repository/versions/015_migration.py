from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
thanks = Table('thanks', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('thanks_author', Integer),
    Column('post_id', Integer),
    Column('timestamp', Date),
)

tags = Table('tags', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('team_tag_id', Integer),
    Column('user_tag_id', Integer),
    Column('body', String(length=200)),
    Column('post_id', Integer),
    Column('tag_author', Integer),
    Column('timestamp', Date),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['thanks'].create()
    post_meta.tables['tags'].columns['timestamp'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['thanks'].drop()
    post_meta.tables['tags'].columns['timestamp'].drop()
