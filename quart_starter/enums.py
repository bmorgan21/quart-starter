from enum import Enum


class EnumStr(str, Enum):
    def __str__(self):
        return self.value


class PostStatus(EnumStr):
    PENDING = "pending"
    PUBLISHED = "published"


class UserRole(EnumStr):
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
