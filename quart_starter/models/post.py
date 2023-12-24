import datetime as dt

from tortoise import Model, fields

from quart_starter import enums

from .helpers import TimestampMixin
from .user import User


class Post(TimestampMixin, Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(128)
    _status = fields.CharEnumField(
        enums.PostStatus,
        max_length=16,
        default=enums.PostStatus.PENDING,
        source_field="status",
    )
    content = fields.TextField()
    published_at = fields.DatetimeField(null=True)
    viewed = fields.IntField(default=0)

    author: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="documents"
    )

    @property
    def status(self):
        return self._status

    def update_status(self, status):
        if status != self._status:
            self._status = status
            if status == enums.PostStatus.PUBLISHED:
                self.published_at = dt.datetime.now(dt.timezone.utc)
            else:
                self.published_at = None
