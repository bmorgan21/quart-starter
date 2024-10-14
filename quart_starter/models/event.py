from tortoise import Model, fields

from quart_starter import enums

from .helpers import TimestampMixin


class Event(TimestampMixin, Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(128)
    data = fields.JSONField()
    status = fields.CharEnumField(
        enums.EventStatus, max_length=16, index=True, default=enums.EventStatus.QUEUED
    )

    worker_id = fields.CharField(max_length=36, null=True)
    num_attempts = fields.IntField(default=0)
    attempted_at = fields.DatetimeField(null=True)
    next_attempt_at = fields.DatetimeField(auto_now_add=True)
    response_code = fields.IntField(null=True)
    response_text = fields.CharField(max_length=256, null=True)
