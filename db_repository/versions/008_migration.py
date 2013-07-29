from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
posts = Table('posts', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('timestamp', Date),
    Column('user_id', Integer),
    Column('parent_post_id', Integer),
    Column('post_body', String),
    Column('reply_body', String),
)

posts = Table('posts', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String(length=140)),
    Column('parent_post_id', Integer),
    Column('timestamp', Date),
    Column('user_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['posts'].columns['post_body'].drop()
    pre_meta.tables['posts'].columns['reply_body'].drop()
    post_meta.tables['posts'].columns['body'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['posts'].columns['post_body'].create()
    pre_meta.tables['posts'].columns['reply_body'].create()
    post_meta.tables['posts'].columns['body'].drop()
