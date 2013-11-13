from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
users = Table('users', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('employee_id', Integer),
    Column('firstname', String),
    Column('lastname', String),
    Column('nickname', String),
    Column('email', String),
    Column('photo', String),
    Column('phone', String),
    Column('username', String),
    Column('manager_id', Integer),
    Column('is_active', Boolean),
)

users = Table('users', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('employee_id', Integer),
    Column('firstname', String(length=64)),
    Column('lastname', String(length=64)),
    Column('nickname', String(length=64)),
    Column('email', String(length=120)),
    Column('photo', String(length=120)),
    Column('phone', String(length=25)),
    Column('username', String(length=68)),
    Column('manager_id', Integer),
    Column('is_deleted', Boolean, nullable=False, default=ColumnDefault(False)),
)

tags = Table('tags', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('team_tag_id', Integer),
    Column('user_tag_id', Integer),
    Column('body', String),
    Column('post_id', Integer),
    Column('tag_author', Integer),
    Column('time', DateTime),
    Column('is_active', Boolean),
)

tags = Table('tags', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('team_tag_id', Integer),
    Column('user_tag_id', Integer),
    Column('body', String(length=200)),
    Column('post_id', Integer),
    Column('tag_author', Integer),
    Column('time', DateTime),
    Column('is_deleted', Boolean, nullable=False, default=ColumnDefault(False)),
)

posts = Table('posts', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String),
    Column('parent_post_id', Integer),
    Column('time', DateTime),
    Column('user_id', Integer),
    Column('photo_link', String),
    Column('is_active', Boolean),
)

posts = Table('posts', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String(length=140)),
    Column('parent_post_id', Integer),
    Column('time', DateTime),
    Column('user_id', Integer),
    Column('photo_link', String(length=140)),
    Column('is_deleted', Boolean, nullable=False, default=ColumnDefault(False)),
)

users_teams = Table('users_teams', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', Integer, nullable=False),
    Column('team_id', Integer, nullable=False),
    Column('is_active', Boolean),
)

users_teams = Table('users_teams', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', Integer, nullable=False),
    Column('team_id', Integer, nullable=False),
    Column('is_deleted', Boolean, nullable=False, default=ColumnDefault(False)),
)

teams = Table('teams', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('teamname', String),
    Column('photo', String),
    Column('is_active', Boolean),
)

teams = Table('teams', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('teamname', String(length=120)),
    Column('photo', String(length=120)),
    Column('is_deleted', Boolean, nullable=False, default=ColumnDefault(False)),
)

thanks = Table('thanks', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('thanks_sender', Integer),
    Column('post_id', Integer),
    Column('time', DateTime),
    Column('is_active', Boolean),
)

thanks = Table('thanks', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('thanks_sender', Integer),
    Column('post_id', Integer),
    Column('time', DateTime),
    Column('is_deleted', Boolean, nullable=False, default=ColumnDefault(False)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['users'].columns['is_active'].drop()
    post_meta.tables['users'].columns['is_deleted'].create()
    pre_meta.tables['tags'].columns['is_active'].drop()
    post_meta.tables['tags'].columns['is_deleted'].create()
    pre_meta.tables['posts'].columns['is_active'].drop()
    post_meta.tables['posts'].columns['is_deleted'].create()
    pre_meta.tables['users_teams'].columns['is_active'].drop()
    post_meta.tables['users_teams'].columns['is_deleted'].create()
    pre_meta.tables['teams'].columns['is_active'].drop()
    post_meta.tables['teams'].columns['is_deleted'].create()
    pre_meta.tables['thanks'].columns['is_active'].drop()
    post_meta.tables['thanks'].columns['is_deleted'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['users'].columns['is_active'].create()
    post_meta.tables['users'].columns['is_deleted'].drop()
    pre_meta.tables['tags'].columns['is_active'].create()
    post_meta.tables['tags'].columns['is_deleted'].drop()
    pre_meta.tables['posts'].columns['is_active'].create()
    post_meta.tables['posts'].columns['is_deleted'].drop()
    pre_meta.tables['users_teams'].columns['is_active'].create()
    post_meta.tables['users_teams'].columns['is_deleted'].drop()
    pre_meta.tables['teams'].columns['is_active'].create()
    post_meta.tables['teams'].columns['is_deleted'].drop()
    pre_meta.tables['thanks'].columns['is_active'].create()
    post_meta.tables['thanks'].columns['is_deleted'].drop()
