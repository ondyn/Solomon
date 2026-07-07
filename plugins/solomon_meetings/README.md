# Solomon Meetings Plugin

Meeting workflow, attendance tracking, and weighted ballot voting for SVJ governance.

## Scope

- Meeting planning with publishable invitations and agenda preparation
- Start-of-meeting owner snapshots so voting rights remain frozen for that meeting
- Attendance event timeline with repeated arrivals and departures during the meeting
- Ballot-type voting by ownership share or units with aggregate ballot counts
- Quorum calculation for meeting validity and per-agenda approval thresholds
- Minutes, exports, invitation tracking, and reusable ballot style definitions

## Meeting and Voting Data Lifecycle

This plugin now separates current style catalog data from meeting history snapshots.

### Vote weight style catalog (global)

- Location: vote-weight-styles list
- Action: Sync current shares (manual) or automatic sync on ownership/share changes
- Result:
  - Every currently used ownership share gets a VoteWeightStyle row.
  - Existing rows that are no longer used by current ownership are kept and marked as historical (Current style = No).
	- Labels and colors are editable only for current styles.
	- Historical styles are read-only.

Use this catalog as the source of label/color definitions for current ownership shares.

### What is snapshotted when a meeting starts

When Start meeting is executed:

1. Owner snapshots are created for the meeting (fixed share numerators/denominators and display names).
2. Ballot type snapshots are created for the meeting (fixed share -> label/color mapping used in that meeting).
3. Meeting quorum baseline is recalculated against meeting snapshots.

After this moment, changing FlatOwner ownerships or editing global VoteWeightStyle labels/colors does not rewrite historical meeting ballot labels/colors or shares.

### Attendance and quorum during the meeting

- Attendance events (arrival/departure) update presence in meeting snapshots.
- Present share and quorum are always calculated from meeting snapshots for meetings that already have snapshots.
- This keeps historical meetings stable even if ownership changes later.

### Ballots tab behavior

- Meeting Ballots tab displays ballot types from meeting snapshots.
- Counts are derived from meeting snapshot holders and current presence state in that meeting timeline.
- Multi-flat owners are grouped by combined share; if a meeting ballot type exists for that combined share, its snapshot label/color is shown.

## Recommended User Workflow

1. Synchronize style catalog:
	- Open vote-weight-styles.
	- Optional: click Sync current shares for immediate recalculation.
	- Automatic synchronization also runs when FlatOwner or Flat share data changes.
	- Review/edit labels and colors for current styles.
2. Prepare meeting:
	- Create meeting and agenda.
	- Verify included buildings and type.
3. Start meeting:
	- Click Start meeting only when ownership and style catalog are ready.
	- This freezes meeting ownership and meeting ballot label/color mapping.
	- While meeting is not finished, snapshots can be manually refreshed from the meeting Ballots tab.
4. Manage live attendance:
	- Use Attendance tab actions to mark arrivals/departures.
	- Quorum and present share update from attendance events.
5. Run voting sessions:
	- Start voting on agenda item.
	- Fill ballot rows and save.
	- Results are stored in AgendaVoteSession and AgendaVoteBallot.
6. Finish meeting:
	- End meeting after quorum and agenda are completed.
7. Export:
	- Use meeting export for attendance timeline, voting details, and weighted totals.

## Practical Rules

- If ownership changed and you need new current styles, run Sync current shares in vote-weight-styles.
- Most ownership/share updates trigger style sync automatically; manual sync is still available.
- Historical meetings keep their original snapshot labels/colors/shares.
- Changing global style colors after a meeting start affects future meetings, not already started ones.
- Historical vote styles cannot be edited.

## Tests

The spreadsheet-backed regression lives in `solomon_meetings/tests/test_vote_report.py`. It recreates the meeting report from `support/Hlasování 4.6.2026-pro Solomon.ods`, checks the calculated attendance and quorum totals, records vote sessions, and verifies that a later attendance change updates the derived values.

Run it from the repository root with:

```bash
docker compose exec netbox python manage.py test solomon_meetings.tests.test_vote_report --keepdb
```

`--keepdb` reuses the existing test database between runs, which makes repeated local test runs faster.

To run the whole meetings plugin test suite, use the same command and replace the module path with `solomon_meetings.tests`.
