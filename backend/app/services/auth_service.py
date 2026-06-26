import hashlib
import secrets
from app.database.db import get_connection


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def login_user(email: str, password: str):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT user_id, name, email
        FROM users
        WHERE email = %s AND password_hash = %s
        """,
        (email, hash_password(password))
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return None

    token = secrets.token_hex(32)

    return {
        "token": token,
        "user": user
    }