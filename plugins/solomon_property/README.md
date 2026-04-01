# Solomon Property Plugin

Property inventory management plugin for NetBox / Solomon.

## Models

- **Building** — Apartment buildings (CUZK integration fields)
- **Flat** — Individual flat units belonging to a building
- **Person** — Contact data store: natural persons (can be owner, tenant, contact, etc.)
- **Owner** — Natural or legal entity owning a flat (links to Persons for contacts)
- **FlatOwner** — M:N junction: flat ↔ owner with share and effective dates
- **Tenant** — Person renting a flat (links to Person records)

## Design Notes

- `Person` is a universal contact data store. An `Owner` can have multiple `Person`
  records (e.g. SJM = two co-owners as separate persons). Same for `Tenant`.
- `Owner` represents the legal ownership entity (natural or legal person, SJM).
- `Person` holds the individual's contact details and can be reused across roles
  (owner contact, tenant, board member, etc.)
