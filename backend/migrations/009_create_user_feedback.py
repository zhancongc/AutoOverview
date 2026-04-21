"""
Migration: 创建 user_feedback 表
"""

def upgrade(session):
    from sqlalchemy import text
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            email VARCHAR(255) DEFAULT '',
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    session.commit()
    print("✅ Created user_feedback table")


def downgrade(session):
    from sqlalchemy import text
    session.execute(text("DROP TABLE IF EXISTS user_feedback"))
    session.commit()
    print("✅ Dropped user_feedback table")


if __name__ == "__main__":
    from database import db
    db.connect()
    with next(db.get_session()) as session:
        upgrade(session)
