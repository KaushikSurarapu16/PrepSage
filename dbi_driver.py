from dataclasses import dataclass
from typing import Optional
from contextlib import contextmanager
import sqlite3

@dataclass
class UserProfile:
    user_id: str
    name: str
    school: str
    interview_status: str

class DatabaseDriver:
    def __init__(self, db_path: str = "assistant_db.sqlite"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create user_profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    school TEXT NOT NULL,
                    interview_status TEXT NOT NULL
                )
            """)
            conn.commit()

    def create_user_profile(self, user_id: str, name: str, school: str, interview_status: str) -> UserProfile:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_profiles (user_id, name, school, interview_status) VALUES (?, ?, ?, ?)",
                (user_id, name, school, interview_status)
            )
            conn.commit()
            return UserProfile(user_id=user_id, name=name, school=school, interview_status=interview_status)

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return UserProfile(
                user_id=row[0],
                name=row[1],
                school=row[2],
                interview_status=row[3]
            )
