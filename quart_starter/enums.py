from enum import Enum


class EnumStr(str, Enum):
    def __str__(self):
        return self.value


class PostStatus(EnumStr):
    DRAFT = "draft"
    PUBLISHED = "published"


class UserRole(EnumStr):
    SYSTEM = "system"
    ADMIN = "admin"
    USER = "user"


class UserStatus(EnumStr):
    PENDING = "pending"
    ACTIVE = "active"


class Permission(EnumStr):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class TokenType(EnumStr):
    WEB = "web"
    API = "api"


class EventStatus(EnumStr):
    QUEUED = "queued"
    PROCESSED = "processed"
    FAILED = "failed"
