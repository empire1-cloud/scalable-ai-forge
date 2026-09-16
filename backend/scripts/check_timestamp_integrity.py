"""
Read-only diagnostic: find blueprints (and users) whose created_at/updated_at
predates this app's own existence.

Context: the code that writes these timestamps (`server.py::_blueprint_doc`,
`rename_blueprint`, `register`) has always used `datetime.now(timezone.utc)`
-- never a hardcoded value, never something read from the LLM's JSON output,
never something a client could supply (verified: `BlueprintCreateIn` and
`BlueprintRenameIn` don't accept a date field at all). A stale date on a live
Vault card is therefore a *bad write*, not a bug in how dates are displayed
or parsed today -- most plausibly a blueprint created while the underlying
container's system clock hadn't finished syncing (or was frozen/restored
from an earlier snapshot) at the moment `datetime.now()` was called. See
`timestamps.py` for the guard against this going forward.

This script does NOT modify anything -- there is no way to recover the true
original creation time of a bad record after the fact, so "fixing" it here
would just replace one wrong guess with another. It reports what it finds so
a human (who may have real context, e.g. "I know that demo account is from
launch week") can decide what to do with it.

Usage:
    cd backend && python scripts/check_timestamp_integrity.py

Reads MONGO_URL / DB_NAME from the environment (same as server.py). Exits
non-zero if it finds anything implausible, so it's safe to wire into a CI or
cron check later without any code changes.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from timestamps import MIN_PLAUSIBLE_YEAR  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _looks_implausible(value) -> bool:
    if not isinstance(value, str):
        return True
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.year < MIN_PLAUSIBLE_YEAR


async def main() -> int:
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    findings = []

    async for bp in db.blueprints.find({}, {"_id": 0, "id": 1, "title": 1, "user_id": 1, "created_at": 1, "updated_at": 1}):
        for field in ("created_at", "updated_at"):
            value = bp.get(field)
            if _looks_implausible(value):
                findings.append(
                    f"blueprint id={bp.get('id')} user_id={bp.get('user_id')} "
                    f"title={bp.get('title')!r} {field}={value!r}"
                )

    async for user in db.users.find({}, {"_id": 0, "id": 1, "email": 1, "created_at": 1}):
        if _looks_implausible(user.get("created_at")):
            findings.append(
                f"user id={user.get('id')} email={user.get('email')} created_at={user.get('created_at')!r}"
            )

    client.close()

    if not findings:
        print(f"OK: no created_at/updated_at before {MIN_PLAUSIBLE_YEAR} found in {db_name}.")
        return 0

    print(f"Found {len(findings)} record(s) with an implausible timestamp (before {MIN_PLAUSIBLE_YEAR}):\n")
    for line in findings:
        print(f"  - {line}")
    print(
        "\nThese were not modified. There is no reliable way to recover the true "
        "original creation time after the fact -- decide manually whether to "
        "correct, annotate, or leave these records."
    )
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
