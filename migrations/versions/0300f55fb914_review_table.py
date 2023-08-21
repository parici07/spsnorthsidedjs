"""review table

Revision ID: 0300f55fb914
Revises: 8968f4d7d0dc
Create Date: 2023-08-21 13:05:51.431639

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0300f55fb914'
down_revision = '8968f4d7d0dc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('song_reviews',
    sa.Column('review_id', sa.Integer(), nullable=False),
    sa.Column('review', sa.String(length=140), nullable=True),
    sa.Column('reviewsong_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], name='song_reviews_user_id'),
    sa.ForeignKeyConstraint(['username'], ['user.username'], name='song_reviews_username'),
    sa.PrimaryKeyConstraint('review_id'),
    sa.UniqueConstraint('review_id')
    )
    with op.batch_alter_table('song_reviews', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_song_reviews_review'), ['review'], unique=False)
        batch_op.create_index(batch_op.f('ix_song_reviews_reviewsong_id'), ['reviewsong_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('song_reviews', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_song_reviews_reviewsong_id'))
        batch_op.drop_index(batch_op.f('ix_song_reviews_review'))

    op.drop_table('song_reviews')
    # ### end Alembic commands ###