# Solomon Issues

QR-coded asset tags and public problem reporting for Solomon.

## What it does

- **Asset tags** - a printable QR label bound to any item: a flat, a water valve,
  a door, an elevator, a common room, or any technical asset. Each tag carries an
  opaque public code, an editable label caption ("Scan me and report a problem"),
  a public description, and routing defaults.
- **Public reporting** - scanning the QR code opens a mobile-friendly public page
  under the same deployment (`/plugins/issues/t/<code>/`). It works on
  `localhost` and on any production hostname because the absolute URL is derived
  from the incoming request unless `public_base_url` is configured.
- **Issue management** - status workflow, priority, assignment to a user or team,
  due dates, resolution text, duplicates, internal vs public replies, and a full
  timeline of every change.
- **Notifications** - managers are notified when a problem is reported or
  updated; reporters receive replies, resolution notices, and a tokenised link to
  follow progress. Every delivery attempt is logged.

## Permissions

Standard NetBox model permissions apply (`view_`, `add_`, `change_`, `delete_`
for `assettag`, `issue`, `issuecategory`, `issuecomment`). In addition:

| Permission | Purpose |
| --- | --- |
| `solomon_issues.manage_issue` | Change status, priority, assignment, resolution |
| `solomon_issues.view_internal_issue` | See internal timeline entries and comments |
| `solomon_issues.report_issue` | Report problems even when anonymous reporting is disabled |
| `solomon_issues.print_assettag` | Render and print the QR label sheet |

Anonymous reporting is controlled by the `allow_anonymous_reports` plugin setting
and the per-tag `allow_public_reports` flag.

## Configuration

```python
PLUGINS_CONFIG = {
    "solomon_issues": {
        "public_base_url": "",              # empty = derive from the request
        "allow_anonymous_reports": True,
        "public_issue_visibility": "open",  # none | open | all
        "public_languages": ["en", "cs"],  # language switcher on public pages
        "default_label_caption": "",        # fallback QR caption; empty = translated default
        "manager_emails": ["spravce@example.com"],
        "notifications_enabled": True,
        "async_notifications": True,
        "qr_error_correction": "M",
        "rate_limit_reports_per_hour": 10,
        "attachments_enabled": True,
        "max_attachment_size_mb": 10,
        "require_reporter_email": False,
    },
}
```

The caption printed next to a QR code comes from the tag's **Label caption**
field. When a tag leaves it blank, `default_label_caption` is used, falling back
to a translated "Scan me and report a problem".

Public pages accept `?lang=<code>` for any language listed in
`public_languages` and remember the choice in the standard Django language
cookie.

## Public URLs

| URL | Purpose |
| --- | --- |
| `/plugins/issues/t/<code>/` | Item page reached by scanning the QR code |
| `/plugins/issues/t/<code>/report/` | Report submission endpoint |
| `/plugins/issues/r/<token>/` | Reporter view of their own issue |
| `/plugins/issues/u/<token>/` | Unsubscribe from issue notifications |
