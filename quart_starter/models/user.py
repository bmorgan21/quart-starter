from tortoise import Model, fields

from quart_starter import enums


class User(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(128, unique=True)
    hashed_password = fields.BinaryField(null=True)
    status = fields.CharEnumField(
        enums.UserStatus, max_length=20, default=enums.UserStatus.ACTIVE
    )
    name = fields.CharField(32, null=True)
    picture = fields.TextField(null=True)
    role = fields.CharEnumField(
        enums.UserRole, max_length=16, default=enums.UserRole.USER
    )

    def __str__(self):
        return f"User {self.id}: {self.status}"
