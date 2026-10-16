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
- Walls, doors, windows, and dimensions are line segments with a draggable
	handle at each end instead of scale and rotation handles. Drag an endpoint
	to change length or direction; hold Shift to keep the line horizontal or
	vertical. New walls use a 3-unit stroke. For a horizontal line, Width is its
	length and Height its thickness; for a vertical line, Width is its thickness
	and Height its length. X and Y are the segment's top-left endpoint. Lines are
	saved as absolute endpoints without rotation or scaling; legacy rotated or
	scaled lines are converted on load without changing where they are drawn.
- SVG export includes visible vector elements and labels at the full plan size,
	without the source drawing or canvas background, independently of viewer zoom.
- Element labels appear centered on shapes in the editor, viewer, and SVG
	export. The Show label on floor plan switch below Label controls visibility
	for each element, including standalone text. Labels are visible by default;
	the setting is saved with the element and retained when duplicating it.
- Select an element in the editor to set Text size and Text orientation
	(0, 90, 180, or 270 degrees) beneath its label. Shape captions rotate
	independently of the shape, relative to its orientation; standalone text
	rotates around its center. Size and orientation persist when saving,
	duplicating, viewing, and exporting SVG. Existing captions default to size 18.
- Borders keep a fixed thickness when shapes are resized, and labels never
	stretch; resizing a text element changes its font size proportionally.
- The editor and viewer render vectors on a Retina-aware canvas; SVG export
	remains vector-based. Shape captions render directly at the canvas resolution
	without bitmap caching, keeping text sharp when zooming or resizing shapes.
- The editor can bring the selected element to front, forward, backward, or
	to back (toolbar or `Shift+]`, `]`, `[`, `Shift+[`); the order is saved.
- The editor's Snap to grid toolbar toggle starts enabled. When enabled, grid dots
	appear and moving, adding, or duplicating unlocked elements snaps their drawn
	geometry (the stroke centerline, not the bounding box) to the nearest 5
	plan-coordinate units: line endpoints and the top-left corner of shapes, so
	walls and room edges meet regardless of stroke width or orientation. Line
	endpoints within 6 screen pixels of another line's endpoint or a room corner
	snap to that point first. Resize handles snap dimensions in 5-unit steps while keeping the opposite
	anchor fixed, including rotated shapes. Proportional resizing preserves the
	aspect ratio and snaps the larger dimension. Rotation snaps in 15-degree steps.
	The grid follows zoom and pan; multi-selections move together. Enabling it
	does not change existing elements or mark the plan changed. Inspector values
	remain exact; the grid is not saved or exported.
- The editor's Align elements to grid toolbar button aligns an existing plan in
	one step: it rounds every unlocked line endpoint to the grid, rounds
	axis-aligned room sizes to 5 units, and moves each room's top-left corner onto
	the grid. Text, circles, and locked elements are unchanged. Save afterwards to
	keep the result.
- Each element has a saved Transparent switch. The Transparent items toolbar
	toggle in the viewer and editor temporarily renders all shapes see-through
	so items hidden behind spaces become visible; it is remembered per browser.
- Versioned plans with source PDF, SVG background, scale, orientation, draft,
	and published revisions.
- The Show source background toolbar toggle in the viewer and editor hides or
	shows the PDF-derived source drawing without changing vector elements or saved
	plan data. The background starts visible on each page load; the toggle is
	disabled when no background is available. SVG export still excludes the source.
- Spaces for flats, rooms, common rooms, cellar cubicles, circulation,
	technical rooms, shafts, and loggias.
- Dated flat-space assignments and independently dated rentals/occupancy.
- Optional spaces-list columns for flat assignments, rentals and occupancy,
	and located technical assets. Enable them through the table's column
	configuration under Available Columns. Assignments and occupancy show only
	records active today (including both date boundaries); technical assets
	include all statuses, matching the space detail page. Each related-record
	column can be sorted by its visible record count. Related records and holders
	respect the user's object-view permissions.
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

Editor, viewer, and label regression tests use Node.js's built-in test runner:

```bash
node --test plugins/solomon_facilities/solomon_facilities/tests/test_editor.js plugins/solomon_facilities/solomon_facilities/tests/test_viewer.js
```

```bash
docker compose exec netbox python manage.py test \
	solomon_facilities.tests.test_models \
	solomon_facilities.tests.test_views \
	solomon_facilities.tests.test_translations \
	solomon_facilities.tests.test_import_command
```

## Localization

English and Czech cover navigation, table headers, floor-plan controls,
tooltips, and dynamically rendered viewer/editor messages. Catalogs belong
under each Python package's `locale/cs/LC_MESSAGES/`, so Django and plugin
wheels can discover them. Older plugins expose their top-level catalogs
through a package-local `locale` symlink.

After changing user-facing strings, extract both translation domains from
the package directory, translate new entries, and compile:

```bash
docker compose exec -w /opt/netbox/plugins_dev/solomon_facilities/solomon_facilities netbox python /opt/netbox/netbox/manage.py makemessages -l cs
docker compose exec -w /opt/netbox/plugins_dev/solomon_facilities/solomon_facilities netbox python /opt/netbox/netbox/manage.py makemessages -l cs -d djangojs
docker compose exec -w /opt/netbox/plugins_dev/solomon_facilities/solomon_facilities netbox python /opt/netbox/netbox/manage.py compilemessages
```

Restart the app after compiling to clear Django's cached translations.
Development startup, production image builds, and plugin publishing compile
catalogs automatically. Do not translate stored object names or drawing labels.