from app.db.session import Base

from .comment import Comment
from .news import News
from .user import User

# Для ruff
__all__ = [
    "Base",
    "Comment",
    "News",
    "User",
]
