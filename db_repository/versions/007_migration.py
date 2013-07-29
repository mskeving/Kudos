from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
replies = Table('replies', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String),
    Column('post_id', Integer),
)

posts = Table('posts', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String),
    Column('timestamp', Date),
    Column('user_id', Integer),
)

posts = Table('posts', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('post_body', String(length=140)),
    Column('reply_body', String(length=140)),
    Column('parent_post_id', Integer),
    Column('timestamp', Date),
    Column('user_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['replies'].drop()
    pre_meta.tables['posts'].columns['body'].drop()
    post_meta.tables['posts'].columns['parent_post_id'].create()
    post_meta.tables['posts'].columns['post_body'].create()
    post_meta.tables['posts'].columns['reply_body'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['replies'].create()
    pre_meta.tables['posts'].columns['body'].create()
    post_meta.tables['posts'].columns['parent_post_id'].drop()
    post_meta.tables['posts'].columns['post_body'].drop()
    post_meta.tables['posts'].columns['reply_body'].drop()
