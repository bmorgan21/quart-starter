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


class Permission(EnumStr):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
