"""Fix database schema - make paper_id nullable in async_tasks table."""
import sqlite3
import os

def fix_database():
    db_path = 'data/scholarlens.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. It will be created automatically.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current schema
    cursor.execute("PRAGMA table_info(async_tasks)")
    columns = cursor.fetchall()
    print("Current async_tasks schema:")
    for col in columns:
        print(f"  {col[1]}: {col[2]} (nullable: {col[3]})")

    # Check if paper_id is NOT NULL
    paper_id_col = next((c for c in columns if c[1] == 'paper_id'), None)
    if paper_id_col and paper_id_col[3] == 1:  # notnull = 1 means NOT NULL
        print("\nFixing paper_id constraint...")

        # SQLite doesn't support ALTER COLUMN, need to recreate table
        # 1. Create new table with correct schema
        cursor.execute('''
            CREATE TABLE async_tasks_new (
                id VARCHAR(36) PRIMARY KEY,
                paper_id VARCHAR(36),
                task_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                progress FLOAT DEFAULT 0.0,
                current_step VARCHAR(200) DEFAULT '',
                result JSON,
                error_message TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')

        # 2. Copy data from old table
        cursor.execute('''
            INSERT INTO async_tasks_new
            SELECT id, paper_id, task_type, status, progress, current_step,
                   result, error_message, created_at, updated_at
            FROM async_tasks
        ''')

        # 3. Drop old table
        cursor.execute('DROP TABLE async_tasks')

        # 4. Rename new table
        cursor.execute('ALTER TABLE async_tasks_new RENAME TO async_tasks')

        conn.commit()
        print("Database schema fixed successfully!")
    else:
        print("\npaper_id is already nullable or column not found.")

    conn.close()

if __name__ == "__main__":
    fix_database()
