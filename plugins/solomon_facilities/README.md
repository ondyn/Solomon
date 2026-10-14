# Solomon Facilities

NetBox plugin for apartment-building schematics, spaces, technical systems,
doors, locks, and physical key custody.

The plugin uses `solomon_property` as the source of truth for buildings,
flats, people, owners, and tenants. It does not duplicate those records.

## Implemented

- Whole-floor viewer with layer filters, zoom, SVG export, object details, and
	click-through navigation.
	Selecting an unlinked shape clears the object details sidebar while keeping
	the shape highlighted. Clicking empty canvas restores the floor-plan details.
- Space detail pages offer View schematic when the space is linked to an
	element in the visible floor-plan revision. The link opens the floor plan
	with the space selected, highlighted, and shown in the details sidebar.
	The button respects floor-plan view permissions; draft-only plans are
	available only to users who can edit plans and revisions.
- Fabric.js vector editor for walls, doors, windows, spaces, labels,
	dimensions, and technical items.
- Element labels appear centered on shapes in the editor, viewer, and SVG
	export. The Show label on floor plan switch below Label controls visibility
	for each element, including standalone text. Labels are visible by default;
	the setting is saved with the element and retained when duplicating it.
- Borders keep a fixed thickness when shapes are resized, and labels never
	stretch; resizing a text element changes its font size proportionally.
- The editor can bring the selected element to front, forward, backward, or
	to back (toolbar or `Shift+]`, `]`, `[`, `Shift+[`); the order is saved.
- Each element has a saved Transparent switch. The Transparent items toolbar
	toggle in the viewer and editor temporarily renders all shapes see-through
	so items hidden behind spaces become visible; it is remembered per browser.
- Versioned plans with source PDF, SVG background, scale, orientation, draft,
	and published revisions.
- Spaces for flats, rooms, common rooms, cellar cubicles, circulation,
	technical rooms, shafts, and loggias.
- Dated flat-space assignments and independently dated rentals/occupancy.
- Optional spaces-list columns for flat assignments, rentals and occupancy,
	and located technical assets. Enable them through the table's column
	configuration under Available Columns. Assignments and occupancy show only
	records active today (including both date boundaries); technical assets
	include all statuses, matching the space detail page. Related records and
	holders respect the user's object-view permissions.
- NetBox-native bulk editing of selected spaces or all spaces matching the
	current filters, with optional field clearing, tag updates, validation,
	and change logging. Space references remain individually editable.
	Type and status default to a blank selection that preserves each selected
	space's existing value, including when the selected values differ.
- Doors, lock cylinders, key profiles, physical key copies, and custody
	history.
- Technical systems, located assets, affected flats/spaces, and directional
	system relationships.
- REST API and NetBox audit/change-log support.
- Schematic tabs on building, flat, and owner detail pages.
- Repeatable initial import from the Salounova source drawings.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the domain design, source analysis,
and future work.

## Local setup

```bash
docker compose up -d --wait netbox
docker compose exec netbox python manage.py migrate solomon_facilities
docker compose exec netbox python manage.py import_salounova_schematics
```

The local Compose override mounts `support/` read-only at
`/opt/netbox/support`. The importer expects the seven PDFs and generated SVG
and positioned-text files under `support/floor-schematics/`.

Regenerate browser backgrounds and label coordinates after replacing a source
PDF:

```bash
for pdf in support/floor-schematics/*.pdf; do name=${pdf:t:r}; pdftocairo -svg "$pdf" "support/floor-schematics/generated/${name}.svg"; pdftotext -bbox-layout "$pdf" "support/floor-schematics/generated/${name}.bbox.html"; done
```

Preview the import without database or media changes:

```bash
docker compose exec netbox python manage.py import_salounova_schematics --dry-run --skip-files
```

## Tests

Viewer selection regression tests use Node.js's built-in test runner:

```bash
node --test plugins/solomon_facilities/solomon_facilities/tests/test_viewer.js
```

```bash
docker compose exec netbox python manage.py test \
	solomon_facilities.tests.test_models \
	solomon_facilities.tests.test_views \
	solomon_facilities.tests.test_import_command
```