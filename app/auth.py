"""
Authentication module for FutureElite
Handles user login, registration, and session management
"""

from flask import session
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional
from .models import User


class UserSession(UserMixin):
    """User session class for Flask-Login"""
    def __init__(self, user: User):
        self.id = user.id
        self.username = user.username
        self.email = user.email
        self._user = user
    
    def get_user(self) -> User:
        """Get the underlying User model"""
        return self._user


def create_user_session(user: User) -> UserSession:
    """Create a UserSession from a User model"""
    return UserSession(user)

