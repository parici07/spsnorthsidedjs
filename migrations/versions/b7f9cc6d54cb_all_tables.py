"""all tables

Revision ID: b7f9cc6d54cb
Revises: 
Create Date: 2023-08-11 12:22:59.175717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f9cc6d54cb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('about_me', sa.String(length=140), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('events',
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('event_name', sa.String(length=64), nullable=True),
    sa.Column('event_code', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], name='fk_user_id'),
    sa.PrimaryKeyConstraint('event_id'),
    sa.UniqueConstraint('event_code'),
    sa.UniqueConstraint('event_id')
    )
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_events_event_name'), ['event_name'], unique=True)

    op.create_table('favourite_song',
    sa.Column('song_id', sa.Integer(), nullable=False),
    sa.Column('track_id', sa.Integer(), nullable=True),
    sa.Column('song_name', sa.String(length=64), nullable=True),
    sa.Column('artist_name', sa.String(length=64), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], name='songs_user_id'),
    sa.PrimaryKeyConstraint('song_id'),
    sa.UniqueConstraint('song_id')
    )
    with op.batch_alter_table('favourite_song', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_favourite_song_artist_name'), ['artist_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_favourite_song_song_name'), ['song_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_favourite_song_track_id'), ['track_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('favourite_song', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_favourite_song_track_id'))
        batch_op.drop_index(batch_op.f('ix_favourite_song_song_name'))
        batch_op.drop_index(batch_op.f('ix_favourite_song_artist_name'))

    op.drop_table('favourite_song')
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_events_event_name'))

    op.drop_table('events')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    # ### end Alembic commands ###
