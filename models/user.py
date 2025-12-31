"""
User Model - Represents application users

This module defines the User data model for the tax application.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """
    Represents a user of the tax application.

    In a real application, this would be connected to an authentication system
    and user database. For now, it's a simple data structure.
    """
    id: str
    name: str
    email: str
    created_date: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True

    def __post_init__(self):
        """Set default values after initialization"""
        if self.created_date is None:
            self.created_date = datetime.now()

    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create user from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            email=data['email'],
            created_date=datetime.fromisoformat(data['created_date']) if data.get('created_date') else None,
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            is_active=data.get('is_active', True)
        )

    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.now()

    def deactivate(self):
        """Deactivate the user account"""
        self.is_active = False

    def activate(self):
        """Activate the user account"""
        self.is_active = True