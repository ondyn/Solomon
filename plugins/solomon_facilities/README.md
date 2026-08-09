# Solomon Facilities

NetBox plugin for apartment-building schematics, spaces, technical systems,
doors, locks, and physical key custody.

The plugin uses `solomon_property` as the source of truth for buildings,
flats, people, owners, and tenants. It does not duplicate those records.

## Implemented

- Whole-floor viewer with layer filters, zoom, SVG export, object details, and
	click-through navigation.
- Fabric.js vector editor for walls, doors, windows, spaces, labels,
	dimensions, and technical items.
- Versioned plans with source PDF, SVG background, scale, orientation, draft,
	and published revisions.
- Spaces for flats, rooms, common rooms, cellar cubicles, circulation,
	technical rooms, shafts, and loggias.
- Dated flat-space assignments and independently dated rentals/occupancy.
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

```bash
docker compose exec netbox python manage.py test \
	solomon_facilities.tests.test_models \
	solomon_facilities.tests.test_views \
	solomon_facilities.tests.test_import_command
```