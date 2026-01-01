"""
Collaboration Service - Handle sharing, comments, and review features

This module provides functionality for:
- Sharing tax returns with spouses and tax preparers
- Managing access permissions and roles
- Adding comments and notes to tax data
- Review mode for collaborative editing
- Audit trail for collaboration activities
"""

import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import os
from pathlib import Path

from services.exceptions import (
    InvalidInputException,
    ServiceExecutionException
)
from services.error_logger import get_error_logger

from services.encryption_service import EncryptionService
from config.app_config import AppConfig
from utils.event_bus import EventBus, Event, EventType

logger = logging.getLogger(__name__)


class CollaborationRole(Enum):
    """Roles for collaboration participants"""
    OWNER = "owner"
    SPOUSE = "spouse"
    TAX_PREPARER = "tax_preparer"
    REVIEWER = "reviewer"


class AccessLevel(Enum):
    """Access levels for shared returns"""
    READ_ONLY = "read_only"
    COMMENT = "comment"
    EDIT = "edit"
    FULL_ACCESS = "full_access"


class ReviewStatus(Enum):
    """Status of tax return review"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Collaborator:
    """Represents a collaborator on a tax return"""
    id: str
    name: str
    email: str
    role: CollaborationRole
    access_level: AccessLevel
    invited_date: datetime
    last_access: Optional[datetime] = None
    invited_by: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['role'] = self.role.value
        data['access_level'] = self.access_level.value
        data['invited_date'] = self.invited_date.isoformat()
        if self.last_access:
            data['last_access'] = self.last_access.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Collaborator':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['role'] = CollaborationRole(data['role'])
        data_copy['access_level'] = AccessLevel(data['access_level'])
        data_copy['invited_date'] = datetime.fromisoformat(data['invited_date'])
        if data.get('last_access'):
            data_copy['last_access'] = datetime.fromisoformat(data['last_access'])
        return cls(**data_copy)


@dataclass
class Comment:
    """Represents a comment or note on tax data"""
    id: str
    tax_year: int
    field_path: str  # Dot-notation path to the field
    content: str
    author_id: str
    author_name: str
    created_date: datetime
    modified_date: Optional[datetime] = None
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_date: Optional[datetime] = None
    parent_comment_id: Optional[str] = None  # For threaded comments
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['created_date'] = self.created_date.isoformat()
        if self.modified_date:
            data['modified_date'] = self.modified_date.isoformat()
        if self.resolved_date:
            data['resolved_date'] = self.resolved_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Comment':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['created_date'] = datetime.fromisoformat(data['created_date'])
        if data.get('modified_date'):
            data_copy['modified_date'] = datetime.fromisoformat(data['modified_date'])
        if data.get('resolved_date'):
            data_copy['resolved_date'] = datetime.fromisoformat(data['resolved_date'])
        return cls(**data_copy)


@dataclass
class SharedReturn:
    """Represents a shared tax return"""
    id: str
    tax_year: int
    owner_id: str
    owner_name: str
    title: str
    description: str
    collaborators: Dict[str, Collaborator]  # id -> collaborator
    comments: Dict[str, Comment]  # id -> comment
    created_date: datetime
    last_modified: datetime
    is_active: bool = True
    share_token: str = ""  # For public sharing links
    settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.settings is None:
            self.settings = {
                'allow_comments': True,
                'allow_editing': False,
                'require_approval': False,
                'notify_on_changes': True
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['collaborators'] = {k: v.to_dict() for k, v in self.collaborators.items()}
        data['comments'] = {k: v.to_dict() for k, v in self.comments.items()}
        data['created_date'] = self.created_date.isoformat()
        data['last_modified'] = self.last_modified.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedReturn':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['collaborators'] = {k: Collaborator.from_dict(v) for k, v in data['collaborators'].items()}
        data_copy['comments'] = {k: Comment.from_dict(v) for k, v in data['comments'].items()}
        data_copy['created_date'] = datetime.fromisoformat(data['created_date'])
        data_copy['last_modified'] = datetime.fromisoformat(data['last_modified'])
        return cls(**data_copy)


class CollaborationService:
    """
    Service for managing collaborative tax return features.

    Handles sharing, permissions, comments, and review functionality.
    """

    def __init__(self, config: AppConfig):
        """
        Initialize the collaboration service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.encryption = EncryptionService(self.config.key_file)
        self.event_bus = EventBus.get_instance()

        # In-memory storage (in production, this would be a database)
        self.shared_returns: Dict[str, SharedReturn] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> user_info

        # Ensure collaboration directory exists
        self.collab_dir = Path(self.config.safe_dir) / "collaboration"
        self.collab_dir.mkdir(exist_ok=True)

        # Load existing shared returns
        self._load_shared_returns()

    def _load_shared_returns(self):
        """Load shared returns from disk"""
        try:
            collab_file = self.collab_dir / "shared_returns.json"
            if collab_file.exists():
                with open(collab_file, 'r') as f:
                    data = json.load(f)
                    for return_id, return_data in data.items():
                        self.shared_returns[return_id] = SharedReturn.from_dict(return_data)
        except Exception as e:
            logger.error(f"Failed to load shared returns: {e}")

    def _save_shared_returns(self):
        """Save shared returns to disk"""
        try:
            collab_file = self.collab_dir / "shared_returns.json"
            data = {k: v.to_dict() for k, v in self.shared_returns.items()}
            with open(collab_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save shared returns: {e}")

    def create_shared_return(self, tax_year: int, owner_id: str, owner_name: str,
                           title: str, description: str = "") -> str:
        """
        Create a new shared return.

        Args:
            tax_year: The tax year for the return
            owner_id: ID of the owner
            owner_name: Name of the owner
            title: Title for the shared return
            description: Optional description

        Returns:
            ID of the created shared return
        """
        return_id = str(uuid.uuid4())

        # Create owner collaborator
        owner = Collaborator(
            id=owner_id,
            name=owner_name,
            email="",  # Owner doesn't need email for themselves
            role=CollaborationRole.OWNER,
            access_level=AccessLevel.FULL_ACCESS,
            invited_date=datetime.now(),
            invited_by=owner_id
        )

        shared_return = SharedReturn(
            id=return_id,
            tax_year=tax_year,
            owner_id=owner_id,
            owner_name=owner_name,
            title=title,
            description=description,
            collaborators={owner_id: owner},
            comments={},
            created_date=datetime.now(),
            last_modified=datetime.now(),
            share_token=str(uuid.uuid4())[:8]  # Short token for sharing
        )

        self.shared_returns[return_id] = shared_return
        self._save_shared_returns()

        logger.info(f"Created shared return {return_id} for tax year {tax_year}")
        self.event_bus.publish(Event(
            type=EventType.TAX_DATA_CHANGED,
            source='CollaborationService',
            data={'action': 'shared_return_created', 'return_id': return_id}
        ))

        return return_id

    def invite_collaborator(self, return_id: str, inviter_id: str, name: str, email: str,
                          role: CollaborationRole, access_level: AccessLevel) -> bool:
        """
        Invite a collaborator to a shared return.

        Args:
            return_id: ID of the shared return
            inviter_id: ID of the person sending the invitation
            name: Name of the collaborator
            email: Email of the collaborator
            role: Role of the collaborator
            access_level: Access level granted

        Returns:
            True if invitation was sent successfully
        """
        if return_id not in self.shared_returns:
            return False

        shared_return = self.shared_returns[return_id]

        # Check if inviter has permission
        if inviter_id not in shared_return.collaborators:
            return False

        inviter = shared_return.collaborators[inviter_id]
        if inviter.access_level != AccessLevel.FULL_ACCESS:
            return False

        # Create collaborator
        collaborator_id = str(uuid.uuid4())
        collaborator = Collaborator(
            id=collaborator_id,
            name=name,
            email=email,
            role=role,
            access_level=access_level,
            invited_date=datetime.now(),
            invited_by=inviter_id
        )

        shared_return.collaborators[collaborator_id] = collaborator
        shared_return.last_modified = datetime.now()
        self._save_shared_returns()

        logger.info(f"Invited collaborator {name} to return {return_id}")
        self.event_bus.publish(Event(
            type=EventType.TAX_DATA_CHANGED,
            source='CollaborationService',
            data={'action': 'collaborator_invited', 'return_id': return_id, 'collaborator_id': collaborator_id}
        ))

        return True

    def add_comment(self, return_id: str, tax_year: int, field_path: str, content: str,
                   author_id: str, author_name: str, parent_comment_id: Optional[str] = None) -> Optional[str]:
        """
        Add a comment to a shared return.

        Args:
            return_id: ID of the shared return
            tax_year: Tax year the comment applies to
            field_path: Path to the field being commented on
            content: Comment content
            author_id: ID of the comment author
            author_name: Name of the comment author
            parent_comment_id: ID of parent comment (for threading)

        Returns:
            ID of the created comment, or None if failed
        """
        if return_id not in self.shared_returns:
            return None

        shared_return = self.shared_returns[return_id]

        # Check if author has permission to comment
        if author_id not in shared_return.collaborators:
            return None

        author = shared_return.collaborators[author_id]
        if author.access_level == AccessLevel.READ_ONLY:
            return None

        # Create comment
        comment_id = str(uuid.uuid4())
        comment = Comment(
            id=comment_id,
            tax_year=tax_year,
            field_path=field_path,
            content=content,
            author_id=author_id,
            author_name=author_name,
            created_date=datetime.now(),
            parent_comment_id=parent_comment_id
        )

        shared_return.comments[comment_id] = comment
        shared_return.last_modified = datetime.now()
        self._save_shared_returns()

        logger.info(f"Added comment {comment_id} to return {return_id}")
        self.event_bus.publish(Event(
            type=EventType.TAX_DATA_CHANGED,
            source='CollaborationService',
            data={'action': 'comment_added', 'return_id': return_id, 'comment_id': comment_id}
        ))

        return comment_id

    def resolve_comment(self, return_id: str, comment_id: str, resolver_id: str, resolver_name: str) -> bool:
        """
        Mark a comment as resolved.

        Args:
            return_id: ID of the shared return
            comment_id: ID of the comment to resolve
            resolver_id: ID of the person resolving
            resolver_name: Name of the person resolving

        Returns:
            True if comment was resolved successfully
        """
        if return_id not in self.shared_returns:
            return False

        shared_return = self.shared_returns[return_id]

        if comment_id not in shared_return.comments:
            return False

        # Check if resolver has permission
        if resolver_id not in shared_return.collaborators:
            return False

        comment = shared_return.comments[comment_id]
        comment.resolved = True
        comment.resolved_by = resolver_name
        comment.resolved_date = datetime.now()

        shared_return.last_modified = datetime.now()
        self._save_shared_returns()

        logger.info(f"Resolved comment {comment_id} in return {return_id}")
        return True

    def get_shared_return(self, return_id: str) -> Optional[SharedReturn]:
        """Get a shared return by ID"""
        return self.shared_returns.get(return_id)

    def get_user_shared_returns(self, user_id: str) -> List[SharedReturn]:
        """Get all shared returns a user has access to"""
        returns = []
        for shared_return in self.shared_returns.values():
            if user_id in shared_return.collaborators:
                returns.append(shared_return)
        return returns

    def get_comments_for_field(self, return_id: str, field_path: str, tax_year: int) -> List[Comment]:
        """Get all comments for a specific field"""
        if return_id not in self.shared_returns:
            return []

        shared_return = self.shared_returns[return_id]
        comments = []

        for comment in shared_return.comments.values():
            if comment.field_path == field_path and comment.tax_year == tax_year:
                comments.append(comment)

        return sorted(comments, key=lambda c: c.created_date)

    def get_threaded_comments(self, return_id: str) -> Dict[str, List[Comment]]:
        """Get comments organized by threads"""
        if return_id not in self.shared_returns:
            return {}

        shared_return = self.shared_returns[return_id]
        threads = {}

        # Group comments by root comment
        for comment in shared_return.comments.values():
            root_id = comment.parent_comment_id or comment.id
            if root_id not in threads:
                threads[root_id] = []
            threads[root_id].append(comment)

        # Sort comments within each thread
        for thread in threads.values():
            thread.sort(key=lambda c: c.created_date)

        return threads

    def update_collaborator_access(self, return_id: str, collaborator_id: str,
                                 new_access_level: AccessLevel, updater_id: str) -> bool:
        """
        Update a collaborator's access level.

        Args:
            return_id: ID of the shared return
            collaborator_id: ID of the collaborator
            new_access_level: New access level
            updater_id: ID of the person making the change

        Returns:
            True if access was updated successfully
        """
        if return_id not in self.shared_returns:
            return False

        shared_return = self.shared_returns[return_id]

        # Check if updater has permission (only owner can change access)
        if updater_id not in shared_return.collaborators:
            return False

        updater = shared_return.collaborators[updater_id]
        if updater.role != CollaborationRole.OWNER:
            return False

        if collaborator_id not in shared_return.collaborators:
            return False

        shared_return.collaborators[collaborator_id].access_level = new_access_level
        shared_return.last_modified = datetime.now()
        self._save_shared_returns()

        logger.info(f"Updated access level for collaborator {collaborator_id} in return {return_id}")
        return True

    def remove_collaborator(self, return_id: str, collaborator_id: str, remover_id: str) -> bool:
        """
        Remove a collaborator from a shared return.

        Args:
            return_id: ID of the shared return
            collaborator_id: ID of the collaborator to remove
            remover_id: ID of the person removing

        Returns:
            True if collaborator was removed successfully
        """
        if return_id not in self.shared_returns:
            return False

        shared_return = self.shared_returns[return_id]

        # Check if remover has permission
        if remover_id not in shared_return.collaborators:
            return False

        remover = shared_return.collaborators[remover_id]
        if remover.role != CollaborationRole.OWNER and remover_id != collaborator_id:
            return False

        if collaborator_id not in shared_return.collaborators:
            return False

        # Cannot remove owner
        if shared_return.collaborators[collaborator_id].role == CollaborationRole.OWNER:
            return False

        del shared_return.collaborators[collaborator_id]
        shared_return.last_modified = datetime.now()
        self._save_shared_returns()

        logger.info(f"Removed collaborator {collaborator_id} from return {return_id}")
        return True

    def export_shared_return(self, return_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a shared return for a user (with appropriate permissions).

        Args:
            return_id: ID of the shared return
            user_id: ID of the user requesting export

        Returns:
            Export data or None if access denied
        """
        if return_id not in self.shared_returns:
            return None

        shared_return = self.shared_returns[return_id]

        if user_id not in shared_return.collaborators:
            return None

        # Return the shared return data
        return shared_return.to_dict()

    def get_collaboration_stats(self, return_id: str) -> Dict[str, Any]:
        """Get collaboration statistics for a shared return"""
        if return_id not in self.shared_returns:
            return {}

        shared_return = self.shared_returns[return_id]

        stats = {
            'total_collaborators': len(shared_return.collaborators),
            'total_comments': len(shared_return.comments),
            'unresolved_comments': len([c for c in shared_return.comments.values() if not c.resolved]),
            'collaborator_roles': {},
            'last_activity': shared_return.last_modified.isoformat()
        }

        # Count roles
        for collaborator in shared_return.collaborators.values():
            role = collaborator.role.value
            stats['collaborator_roles'][role] = stats['collaborator_roles'].get(role, 0) + 1

        return stats

    # Additional methods for test compatibility and GUI integration

    def invite_user(self, return_id: str, tax_year: int, inviter_id: str, inviter_name: str,
                   invitee_email: str, role: CollaborationRole, access_level: AccessLevel,
                   message: str = "") -> bool:
        """
        Invite a user to collaborate (alias for invite_collaborator with email).

        This is a wrapper around invite_collaborator for GUI compatibility.
        """
        # For now, we'll use a placeholder name since we don't have user lookup
        placeholder_name = invitee_email.split('@')[0].replace('.', ' ').title()

        return self.invite_collaborator(
            return_id=return_id,
            inviter_id=inviter_id,
            name=placeholder_name,
            email=invitee_email,
            role=role,
            access_level=access_level
        )

    def get_shared_users(self, return_id: str) -> List[SharedReturn]:
        """
        Get list of shared returns for a return ID.

        This returns a list with the shared return data for compatibility.
        """
        shared_return = self.get_shared_return(return_id)
        return [shared_return] if shared_return else []

    def update_access_level(self, return_id: str, email: str, new_level: AccessLevel) -> bool:
        """
        Update access level for a user by email.

        This finds the collaborator by email and updates their access level.
        """
        shared_return = self.get_shared_return(return_id)
        if not shared_return:
            return False

        # Find collaborator by email
        for collab_id, collaborator in shared_return.collaborators.items():
            if collaborator.email == email:
                return self.update_collaborator_access(
                    return_id=return_id,
                    collaborator_id=collab_id,
                    new_access_level=new_level,
                    updater_id=shared_return.owner_id  # Assume owner is updating
                )

        return False

    def revoke_access(self, return_id: str, email: str) -> bool:
        """
        Revoke access for a user by email.

        This finds the collaborator by email and removes them.
        """
        shared_return = self.get_shared_return(return_id)
        if not shared_return:
            return False

        # Find collaborator by email
        for collab_id, collaborator in shared_return.collaborators.items():
            if collaborator.email == email:
                return self.remove_collaborator(
                    return_id=return_id,
                    collaborator_id=collab_id,
                    remover_id=shared_return.owner_id  # Assume owner is removing
                )

        return False

    def generate_share_link(self, return_id: str, user_id: str, tax_year: int) -> str:
        """
        Generate a share link for a tax return.

        Returns a placeholder link for now.
        """
        shared_return = self.get_shared_return(return_id)
        if not shared_return:
            return ""

        # Generate a simple share link
        base_url = "https://taxapp.example.com/share"
        token = shared_return.share_token or "placeholder"
        return f"{base_url}/{return_id}/{token}"

    def get_review_status(self, return_id: str, tax_year: int) -> ReviewStatus:
        """
        Get the review status for a tax return.

        For now, returns PENDING as a placeholder.
        """
        return ReviewStatus.PENDING

    def update_review_status(self, return_id: str, tax_year: int, status: ReviewStatus,
                           user_id: str, user_name: str, reason: str = "") -> bool:
        """
        Update the review status for a tax return.

        Placeholder implementation - in a real system this would be stored.
        """
        logger.info(f"Updated review status for return {return_id} to {status.value}")
        return True

    def get_review_notes(self, return_id: str, tax_year: int) -> Optional[str]:
        """
        Get review notes for a tax return.

        Placeholder implementation.
        """
        return "Review notes placeholder"

    def save_review_notes(self, return_id: str, tax_year: int, notes: str,
                        user_id: str, user_name: str) -> bool:
        """
        Save review notes for a tax return.

        Placeholder implementation.
        """
        logger.info(f"Saved review notes for return {return_id}")
        return True

    def export_comments(self, return_id: str, tax_year: int) -> List[Dict[str, Any]]:
        """
        Export all comments for a tax return.

        Returns comments in a format suitable for export.
        """
        shared_return = self.get_shared_return(return_id)
        if not shared_return:
            return []

        comments_data = []
        for comment in shared_return.comments.values():
            if comment.tax_year == tax_year:
                comments_data.append({
                    'id': comment.id,
                    'field_path': comment.field_path,
                    'content': comment.content,
                    'author_name': comment.author_name,
                    'created_date': comment.created_date.isoformat(),
                    'resolved': comment.resolved
                })

        return comments_data

    def get_all_comments_for_return(self, return_id: str, tax_year: int) -> List[Comment]:
        """
        Get all comments for a return and tax year.

        This is an alias for getting comments across all fields.
        """
        shared_return = self.get_shared_return(return_id)
        if not shared_return:
            return []

        return [comment for comment in shared_return.comments.values()
                if comment.tax_year == tax_year]