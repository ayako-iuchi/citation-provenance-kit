"""Tests for tools/statuslog.py and tools/migrate_register.py (kit v1.3).

Run: python3 -m pytest tests
"""
import hashlib
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import statuslog  # noqa: E402

LOG = os.path.join(ROOT, "register", "status_log.jsonl")
NTA = "Japan — NTA Q&A on electronic books (books and documents)"


@pytest.fixture
def log():
    return statuslog.load(LOG)


# --- the two questions -------------------------------------------------------

def test_believed_on_reproduces_what_was_recorded_then(log):
    """On 11 October the log still said one practitioner report; on 12 October, two."""
    then = statuslog.believed_on(log, NTA, "edition", "2026-10-11")
    now = statuslog.believed_on(log, NTA, "edition", "2026-10-12")
    assert then["id"] == "2026-10-10-04"
    assert "a practitioner report (C)" in then["note"]
    assert now["id"] == "2026-10-12-01"
    assert "Two practitioner reports" in now["value"]


def test_nothing_was_believed_before_the_first_record(log):
    assert statuslog.believed_on(log, NTA, "edition", "2026-10-09") is None
    assert statuslog.current(log, NTA, "edition", "2026-10-09")["status"] == "no-record"


def test_expired_status_returns_null_not_the_old_value(log):
    """After its expiry the Rule 4 row yields no value, not 'November 2026'."""
    rule4 = "India — DPDP Rules 2025, Rule 4 (consent managers)"
    before = statuslog.current(log, rule4, "commencement", "2026-10-31")
    after = statuslog.current(log, rule4, "commencement", "2026-11-02")
    assert before["status"] == "ok" and before["value"].startswith("Twelve months")
    assert after["status"] == "expired"
    assert after["value"] is None
    assert after["assertion"]["id"] == "2026-10-10-02"  # still on record, still traceable


def test_no_stated_expiry_is_reported_not_treated_as_permanent(log):
    cg = "Japan — Corporate Governance Code (July 2026), English edition"
    r = statuslog.current(log, cg, "edition", "2030-01-01")
    assert r["status"] == "no-expiry-stated"


def test_a_null_value_is_a_valid_answer():
    """'Looked, and could not establish it' is recorded as null and returned as null."""
    log = [{"id": "x1", "subject": "s", "component": "edition", "value": None, "grade": "—",
            "recorded_on": "2026-10-12", "source": "issuer page", "expires_on": "2026-12-31"}]
    r = statuslog.current(log, "s", "edition", "2026-10-13")
    assert r["status"] == "ok" and r["value"] is None


# --- the log itself ------------------------------------------------------------

def test_log_is_consistent(log):
    assert statuslog.check(log) == []


def test_the_newer_finding_supersedes_without_editing_the_older(log):
    old = next(a for a in log if a["id"] == "2026-10-10-04")
    new = next(a for a in log if a["id"] == "2026-10-12-01")
    assert new["supersedes"] == old["id"]
    assert old["note"].startswith("Conflict: a practitioner report (C)")  # unchanged


def test_append_only_check_catches_an_edit(tmp_path):
    old = tmp_path / "old.jsonl"
    new = tmp_path / "new.jsonl"
    old.write_text('{"id":"a"}\n{"id":"b"}\n', encoding="utf-8")
    new.write_text('{"id":"a"}\n{"id":"b"}\n{"id":"c"}\n', encoding="utf-8")
    assert statuslog.verify_append(old, new)
    new.write_text('{"id":"a"}\n{"id":"B"}\n{"id":"c"}\n', encoding="utf-8")
    assert not statuslog.verify_append(old, new)


def test_log_lines_match_the_schema(log):
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "status_assertion.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    for a in log:
        jsonschema.validate(a, schema)


def test_snapshot_hash_matches_its_wording():
    with open(os.path.join(ROOT, "register", "snapshots.json"), encoding="utf-8") as f:
        snaps = json.load(f)
    for s in snaps:
        assert hashlib.sha256(s["wording"].encode("utf-8")).hexdigest() == s["wording_sha256"]


def test_snapshots_match_the_schema():
    jsonschema = pytest.importorskip("jsonschema")
    with open(os.path.join(ROOT, "schema", "snapshot.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    with open(os.path.join(ROOT, "register", "snapshots.json"), encoding="utf-8") as f:
        for s in json.load(f):
            jsonschema.validate(s, schema)


# --- migration -----------------------------------------------------------------

def test_migration_reproduces_the_first_five_lines():
    """The first lines of the log are exactly what migrate_register.py makes of the v1.1 register."""
    out = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "migrate_register.py"),
         os.path.join(ROOT, "csv", "register_in_motion_template.csv")],
        capture_output=True, text=True, check=True).stdout.splitlines()
    with open(LOG, encoding="utf-8") as f:
        logged = [l.rstrip("\n") for l in f if l.strip()]
    assert logged[: len(out)] == out
    assert len(out) == 5


def test_migration_invents_no_expiry():
    import migrate_register as m
    import datetime as dt
    d = dt.date(2026, 10, 10)
    assert m.expiry("On any change to the page", d) is None
    assert m.expiry("2027-01", d) == dt.date(2027, 1, 1)
    assert m.expiry("November 2026", d) == dt.date(2026, 11, 1)
    assert m.expiry("Monthly; and on any MeitY notification", d) == dt.date(2026, 11, 10)
    assert m.expiry("Each June–July", d) == dt.date(2027, 6, 1)


def test_snapshots_cannot_carry_status():
    """Status lives only in the log, so text indexed from snapshots never holds a status that can go stale."""
    with open(os.path.join(ROOT, "schema", "snapshot.schema.json"), encoding="utf-8") as f:
        schema = json.load(f)
    assert schema["additionalProperties"] is False
    status_words = {"commencement", "in_force", "current", "status", "expires_on", "existence", "dependency"}
    assert not status_words & set(schema["properties"])
