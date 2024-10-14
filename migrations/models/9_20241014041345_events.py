from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "event" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(128) NOT NULL,
    "data" JSONB NOT NULL,
    "status" VARCHAR(16) NOT NULL  DEFAULT 'queued',
    "worker_id" VARCHAR(36),
    "num_attempts" INT NOT NULL  DEFAULT 0,
    "attempted_at" TIMESTAMPTZ,
    "next_attempt_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "response_code" INT,
    "response_text" VARCHAR(256)
);
CREATE INDEX IF NOT EXISTS "idx_event_status_69f524" ON "event" ("status");
COMMENT ON COLUMN "event"."status" IS 'QUEUED: queued\nPROCESSED: processed\nFAILED: failed';
        ALTER TABLE "user" ALTER COLUMN "role" TYPE VARCHAR(16) USING "role"::VARCHAR(16);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "role" TYPE VARCHAR(16) USING "role"::VARCHAR(16);
        DROP TABLE IF EXISTS "event";"""
