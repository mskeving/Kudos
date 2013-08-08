from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
thanks = Table('thanks', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('thanks_author', Integer),
    Column('post_id', Integer),
    Column('timestamp', Date),
)

thanks = Table('thanks', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('thanks_sender', Integer),
    Column('post_id', Integer),
    Column('timestamp', Date),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['thanks'].columns['thanks_author'].drop()
    post_meta.tables['thanks'].columns['thanks_sender'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['thanks'].columns['thanks_author'].create()
    post_meta.tables['thanks'].columns['thanks_sender'].drop()
