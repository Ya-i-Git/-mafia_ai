# backend/db/alembic/versions/001_initial_migration.py
"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Создаем ENUM типы
    userrole_enum = ENUM('admin', 'player', name='userrole', create_type=False)
    userrole_enum.create(op.get_bind(), checkfirst=True)
    
    gamerole_enum = ENUM('mafia', 'don', 'sheriff', 'doctor', 'civilian', name='gamerole', create_type=False)
    gamerole_enum.create(op.get_bind(), checkfirst=True)
    
    # Таблица users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('role', sa.Enum('admin', 'player', name='userrole'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Таблица game_sessions
    op.create_table(
        'game_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('game_id', sa.String(20), nullable=False),
        sa.Column('world', sa.String(50), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('winner', sa.String(20), nullable=True),
        sa.Column('total_players', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_sessions_game_id'), 'game_sessions', ['game_id'], unique=True)
    
    # Таблица game_stats
    op.create_table(
        'game_stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_session_id', sa.Integer(), nullable=False),
        sa.Column('game_role', sa.Enum('mafia', 'don', 'sheriff', 'doctor', 'civilian', name='gamerole'), nullable=False),
        sa.Column('is_winner', sa.Boolean(), nullable=True),
        sa.Column('survived', sa.Boolean(), nullable=True),
        sa.Column('killed_by_mafia', sa.Boolean(), nullable=True),
        sa.Column('killed_by_lynching', sa.Boolean(), nullable=True),
        sa.Column('sheriff_checks_count', sa.Integer(), nullable=True),
        sa.Column('doctor_heals_count', sa.Integer(), nullable=True),
        sa.Column('mafia_kills_count', sa.Integer(), nullable=True),
        sa.Column('don_checks_count', sa.Integer(), nullable=True),
        sa.Column('votes_cast', sa.Integer(), nullable=True),
        sa.Column('correct_votes', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['game_session_id'], ['game_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица player_actions
    op.create_table(
        'player_actions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_session_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('phase', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('was_successful', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['game_session_id'], ['game_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица game_events
    op.create_table(
        'game_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('game_session_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', sa.Text(), nullable=True),
        sa.Column('day_number', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['game_session_id'], ['game_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица user_sessions
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_token'), 'user_sessions', ['token'], unique=True)

def downgrade() -> None:
    op.drop_table('user_sessions')
    op.drop_table('game_events')
    op.drop_table('player_actions')
    op.drop_table('game_stats')
    op.drop_table('game_sessions')
    op.drop_table('users')
    
    # Удаляем ENUM типы
    ENUM(name='gamerole').drop(op.get_bind(), checkfirst=True)
    ENUM(name='userrole').drop(op.get_bind(), checkfirst=True)