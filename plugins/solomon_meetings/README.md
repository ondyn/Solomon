# Solomon Meetings Plugin

Meeting workflow, attendance tracking, and weighted ballot voting for SVJ governance.

## Scope

- Meeting planning with publishable invitations and agenda preparation
- Start-of-meeting owner snapshots so voting rights remain frozen for that meeting
- Attendance event timeline with repeated arrivals and departures during the meeting
- Ballot-type voting by ownership share or units with aggregate ballot counts
- Quorum calculation for meeting validity and per-agenda approval thresholds
- Minutes, exports, invitation tracking, and reusable ballot style definitions

## Tests

The spreadsheet-backed regression lives in `solomon_meetings/tests/test_vote_report.py`. It recreates the meeting report from `support/Hlasování 4.6.2026-pro Solomon.ods`, checks the calculated attendance and quorum totals, records vote sessions, and verifies that a later attendance change updates the derived values.

Run it from the repository root with:

```bash
docker compose exec netbox python manage.py test solomon_meetings.tests.test_vote_report --keepdb
```

`--keepdb` reuses the existing test database between runs, which makes repeated local test runs faster.

To run the whole meetings plugin test suite, use the same command and replace the module path with `solomon_meetings.tests`.
