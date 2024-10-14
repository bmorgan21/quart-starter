import datetime as dt
from typing import List, Union

import requests
from requests.exceptions import RequestException

from quart_starter import enums, models, schemas, settings
from quart_starter.lib.error import ActionError, ForbiddenActionError

from .helpers import conditional_set, handle_orm_errors

MAX_NUM_ATTEMPTS = 5


def has_permission(
    user: schemas.User,
    _obj: Union[schemas.Event, None],
    permission: enums.Permission,
) -> bool:
    if permission == enums.Permission.CREATE:
        return True

    if permission == enums.Permission.READ:
        if user.role == enums.UserRole.ADMIN:
            return True
        return True

    if permission == enums.Permission.UPDATE:
        if user.role == enums.UserRole.ADMIN:
            return True
        return True

    if permission == enums.Permission.DELETE:
        if user.role == enums.UserRole.ADMIN:
            return True
        return False

    return False


@handle_orm_errors
async def get(
    user: schemas.User, id: int = None, options: schemas.EventGetOptions = None
) -> schemas.Event:
    event = None
    if id:
        event = await models.Event.get(id=id)
    else:
        raise ActionError("missing lookup key", type="not_found")

    if not has_permission(
        user, schemas.Event.model_validate(event), enums.Permission.READ
    ):
        raise ForbiddenActionError()

    if options:
        if options.resolves:
            await event.fetch_related(*options.resolves)

    return schemas.Event.model_validate(event)


@handle_orm_errors
async def query(_user: schemas.User, q: schemas.EventQuery) -> schemas.EventResultSet:
    qs = models.Event.all()
    queryset, pagination = await q.apply(qs)

    return schemas.EventResultSet(
        pagination=pagination,
        events=[schemas.Event.model_validate(event) for event in await queryset],
    )


@handle_orm_errors
async def create(user: schemas.User, data: schemas.EventCreate) -> schemas.Event:
    if not has_permission(user, None, enums.Permission.CREATE):
        raise ForbiddenActionError()

    event = await models.Event.create(
        name=data.name, data=data.data, status=data.status
    )

    await event.save()

    return schemas.Event.model_validate(event)


@handle_orm_errors
async def delete(user: schemas.User, id: int) -> None:
    event = await models.Event.get(id=id)

    if not has_permission(
        user, schemas.Event.model_validate(event), enums.Permission.DELETE
    ):
        raise ForbiddenActionError()

    await event.delete()


@handle_orm_errors
async def update(
    user: schemas.User, id: int, data: schemas.EventPatch
) -> schemas.Event:
    event = await models.Event.get(id=id)

    if not has_permission(
        user, schemas.Event.model_validate(event), enums.Permission.UPDATE
    ):
        raise ForbiddenActionError()

    conditional_set(event, "status", data.status)
    conditional_set(event, "num_attempts", data.num_attempts)
    conditional_set(event, "worker_id", data.worker_id)
    conditional_set(event, "next_attempt_at", data.next_attempt_at)

    await event.save()

    return schemas.Event.model_validate(event)


@handle_orm_errors
async def reset_abandoned(_user: schemas.User):
    now = dt.datetime.now(dt.timezone.utc)

    qs = models.Event.filter(
        status=enums.EventStatus.QUEUED,
        worker_id__not_isnull=True,
        modified_at__lte=now - dt.timedelta(minutes=3),
    )

    events = await qs
    if events:
        for event in events:
            event.worker_id = None

        await models.Event.bulk_update(events, fields=["worker_id"])


@handle_orm_errors
async def reserve_for_worker(_user: schemas.User, worker_id: str, limit=5) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    qs = (
        models.Event.filter(
            status=enums.EventStatus.QUEUED,
            worker_id__isnull=True,
            next_attempt_at__lte=now,
        )
        .limit(limit)
        .order_by("next_attempt_at")
    )

    events = await qs
    if events:
        for event in events:
            event.worker_id = worker_id

        await models.Event.bulk_update(events, fields=["worker_id"])


@handle_orm_errors
async def reserved_for_worker(
    _user: schemas.User, worker_id: str
) -> List[schemas.Event]:
    qs = models.Event.filter(status=enums.EventStatus.QUEUED, worker_id=worker_id)

    return [schemas.Event.model_validate(event) for event in await qs]


@handle_orm_errors
async def worker_webhook(_user: schemas.User, id: int, worker_id: str) -> bool:
    event = await models.Event.get(id=id).select_for_update()

    if worker_id != event.worker_id:
        return

    event.num_attempts += 1
    event.attempted_at = dt.datetime.now(dt.timezone.utc)
    event.next_attempt_at = event.attempted_at + dt.timedelta(
        minutes=(2 * (event.num_attempts - 1) + 1)
    )
    await event.save()

    def handle_failure(event):
        if event.num_attempts == MAX_NUM_ATTEMPTS:
            event.status = enums.EventStatus.FAILED
        else:
            event.worker_id = None

    try:
        r = requests.post(
            settings.WEBHOOK_URL,
            json={"name": event.name, "data": event.data},
            timeout=5,
        )
        event.response_code = r.status_code
        event.response_text = r.text[:256]

        if r.status_code == 200 and r.text.strip() == "OK":
            event.status = enums.EventStatus.PROCESSED
        else:
            handle_failure(event)
    except RequestException as e:
        event.response_code = -1
        event.response_text = str(e)[:256]
        handle_failure(event)
    finally:
        await event.save()
