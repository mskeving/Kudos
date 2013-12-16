from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
posts = Table('posts', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String(length=500)),
    Column('parent_post_id', Integer),
    Column('time', DateTime),
    Column('user_id', Integer),
    Column('photo_link', String(length=140)),
    Column('photo_url_fullsize', String(length=140)),
    Column('is_deleted', Boolean, nullable=False, default=ColumnDefault(False)),
    Column('status', Integer, nullable=False, default=ColumnDefault(0)),
    Column('status_committer', String(length=140)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['posts'].columns['status_committer'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['posts'].columns['status_committer'].drop()
