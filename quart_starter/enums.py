from enum import Enum


class EnumStr(str, Enum):
    def __str__(self):
        return self.value


class PostStatusEnum(EnumStr):
    PENDING = "pending"
    PUBLISHED = "published"


class UserRoleEnum(EnumStr):
    ADMIN = "admin"
    USER = "user"
