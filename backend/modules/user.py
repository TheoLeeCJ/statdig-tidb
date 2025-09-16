import os
from typing import Optional, Dict, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
from sql import execute_query

ph = PasswordHasher()
serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY", "fallback-secret-key"))

class User:
    def __init__(self, username: str, email: str, role: str, is_active: bool = True):
        self.username = username
        self.email = email
        self.role = role
        self.is_active = is_active

def hash_password(password: str) -> str:
    """Hash password using Argon2"""
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        ph.verify(hashed, password)
        return True
    except VerifyMismatchError:
        return False

def create_user(username: str, email: str, password: str, role: str = "user") -> Optional[str]:
    """Create a new user and return username"""
    password_hash = hash_password(password)
    
    query = """
        INSERT INTO users (username, email, password_hash, role) 
        VALUES (%s, %s, %s, %s)
    """
    
    try:
        result = execute_query(query, (username, email, password_hash, role))
        if result > 0:
            return username
        return None
    except Exception:
        return None

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user and return User object"""
    user_data = execute_query(
        "SELECT username, email, password_hash, role, is_active FROM users WHERE username = %s",
        (username,),
        fetch_one=True
    )
    
    if not user_data or not user_data['is_active']:
        return None
    
    if verify_password(password, user_data['password_hash']):
        return User(
            username=user_data['username'],
            email=user_data['email'],
            role=user_data['role'],
            is_active=user_data['is_active']
        )
    
    return None

def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username"""
    user_data = execute_query(
        "SELECT username, email, role, is_active FROM users WHERE username = %s",
        (username,),
        fetch_one=True
    )
    
    if user_data and user_data['is_active']:
        return User(
            username=user_data['username'],
            email=user_data['email'],
            role=user_data['role'],
            is_active=user_data['is_active']
        )
    
    return None

def generate_token(user: User) -> str:
    """Generate authentication token"""
    payload = {
        "username": user.username,
        "role": user.role,
        "exp": (datetime.utcnow() + timedelta(hours=int(os.getenv("TOKEN_EXPIRE_HOURS", 24)))).timestamp()
    }
    return serializer.dumps(payload)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode authentication token"""
    try:
        payload = serializer.loads(token, max_age=int(os.getenv("TOKEN_EXPIRE_HOURS", 24)) * 3600)
        if payload.get("exp", 0) < datetime.utcnow().timestamp():
            return None
        return payload
    except Exception:
        return None

def list_users() -> list:
    """List all users (admin only)"""
    return execute_query(
        "SELECT username, email, role, created_at, is_active FROM users ORDER BY created_at DESC",
        fetch_all=True
    ) or []