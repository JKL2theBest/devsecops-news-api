import enum


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    VERIFIED_AUTHOR = "verified_author"
    USER = "user"
