# Solomon - Implementation Roadmap

_Generated: 2026-04-10. Based on todo.txt analysis and design clarification._

---

## Clarifications Captured

| Question | Decision |
|----------|----------|
| Plugin eshop | SaaS marketplace - Solomon will be sold as a commercial product to other SVJ communities |
| Public CMS | Custom Solomon NetBox plugin (stays inside the app, not a standalone CMS) |
| SVJ vs Housing Cooperative | SVJ first; architect so BD (Bytove Druzstvo) can be added later without breaking changes |
| Commercialization | Yes - commercial SaaS product with paid licensing |
| First priority | Meeting management + Voting |

---

## Plugin Overview

| Plugin | Package | Status | Phase |
|--------|---------|--------|-------|
| Core (UI, module hiding, middleware) | `solomon_core` | Done | 1 |
| Property (buildings, flats, owners, tenants) | `solomon_property` | Done | 1 |
| Theme | `solomon_theme` | Done | 1 |
| **Meeting management + Voting** | `solomon_meetings` | **Implemented** | 2 |
| Technical equipment management | `solomon_equipment` | Planned | 3 |
| Equipment inspection manager | `solomon_inspection` | Planned | 3 |
| Common property management | `solomon_commons` | Planned | 4 |
| Access management (keys, tags) | `solomon_access` | Planned | 4 |
| Energy consumption manager | `solomon_energy` | Planned | 4 |
| Task / issue tracking | `solomon_tasks` | Planned | 5 |
| Tender management | `solomon_tenders` | Planned | 5 |
| Public CMS | `solomon_cms` | Planned | 6 |
| SaaS marketplace + licensing | `solomon_saas` | Planned | 7 |
| Backup / restore | `solomon_backup` | Planned | 7 |
| In-app bug reporting | `solomon_support` | Planned | 7 |
| DB cleanup management command | _(in solomon_core)_ | **Implemented** | 2 |

Phases 2-5 are for the current SVJ (Salounova) deployment.  
Phases 6-7 are the commercial/SaaS product expansion.

---

## General Cross-Cutting Rules (apply to every plugin)

1. **No hardcoded type lists.** Every categorical list (device types, energy types, inspection categories, access levels, task categories, tender specialties) must be a configurable model, not an enum or fixed `choices` list. Admins can add new types without code changes.
2. **Dashboard widget for every plugin** where a summary or alert makes sense (upcoming inspections, approaching warranty expiry, pending meeting, overdue tasks, unresolved repairs).
3. **All models use `NetBoxModel`** (UUID pk, timestamps, change log, journaling) - same as `solomon_property`.
4. **Every new plugin follows the same directory structure** as `solomon_property` (models, views, forms, tables, filtersets, urls, navigation, api/, templates/, tests/, migrations/).
5. **Czech-first UI** - all `verbose_name`, help_text, and template labels use `gettext_lazy(_(...))`.

---

## Phase 2 - Meeting Management + Voting (`solomon_meetings`)

Priority: **Highest - required for SVJ governance.**  
Czech legal basis: Civil Code ss. 1208-1215, SVJ statutes.

### Purpose

Manage the full owner-meeting workflow for SVJ assemblies: planning, invitation publishing, meeting start, attendance timeline, weighted ballot voting, minutes, and export.

### Models

#### `MeetingType` (configurable)
| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField | e.g. "Schuze shromazdeni", "Schuze vyboru" |
| `quorum_type` | CharField choices | `BY_UNITS` / `BY_SHARE` |
| `default_quorum_threshold` | DecimalField | e.g. 0.50 (50%) |

#### `Meeting`
| Field | Type | Notes |
|-------|------|-------|
| `meeting_type` | FK MeetingType | |
| `title` | CharField | |
| `buildings` | M2M Building | which buildings are summoned |
| `date_time` | DateTimeField | |
| `location` | CharField | |
| `status` | CharField choices | keep compatibility with NetBox list/detail views |
| `phase` | CharField choices | `PLANNING / IN_PROGRESS / FINISHED` |
| `quorum_threshold` | DecimalField | meeting-level threshold for usnasenischopnost |
| `quorum_achieved` | BooleanField | recalculated during meeting |
| `quorum_updated_at` | DateTimeField | when quorum was last recalculated |
| `started_at` | DateTimeField | actual meeting start |
| `ended_at` | DateTimeField | actual meeting end |
| `invitation_pdf_generated_at` | DateTimeField | latest PDF generation timestamp |
| `invitation_published_at` | DateTimeField | latest CMS publication timestamp |
| `owner_snapshot_taken_at` | DateTimeField | freezes owners and voting rights for that meeting |
| `moderator` | FK User | |
| `note` | TextField | |

**Rule:** Starting a meeting creates a point-in-time snapshot of owners, their shares, and assigned ballot types. Later ownership changes must not affect the already started meeting.

#### `AgendaItem`
| Field | Type | Notes |
|-------|------|-------|
| `meeting` | FK Meeting | |
| `order` | PositiveIntegerField | drag-to-reorder in UI |
| `title` | CharField | |
| `description` | TextField | text of the point / podklad / usneseni |
| `presenter` | CharField | person who presents the point |
| `voting_required` | BooleanField | |
| `voting_method` | CharField choices | `BY_UNITS / BY_SHARE` |
| `quorum_threshold` | DecimalField | minimum meeting quorum needed to vote this point |
| `minimum_pass_percentage` | DecimalField | threshold for passing the proposal |
| `result` | CharField choices | `APPROVED / REJECTED / DEFERRED / N/A` |

**Rule:** Agenda items remain editable and reorderable even after planning. New items may still be added during the meeting if the chair decides so.

#### `MeetingOwnerSnapshot`
| Field | Type | Notes |
|-------|------|-------|
| `meeting` | FK Meeting | |
| `owner` | FK Owner | (from solomon_property) |
| `flat_owner` | FK FlatOwner | ownership record frozen for this meeting |
| `owner_display_name` | CharField | denormalized display value for later exports |
| `flat_label` | CharField | denormalized flat/unit label |
| `representation` | CharField choices | `PRESENT / PROXY / ABSENT` |
| `proxy_name` | CharField | if represented by proxy |
| `share_numerator` | PositiveIntegerField | frozen ownership share numerator |
| `share_denominator` | PositiveIntegerField | frozen ownership share denominator |
| `share_value` | DecimalField | precomputed share weight |
| `unit_count` | PositiveIntegerField | number of voting units |
| `ballot_label` | CharField | text/number/letter shown on ballot card |
| `ballot_color` | CharField | ballot color |
| `snapshot_taken_at` | DateTimeField | |
| `first_arrived_at` | DateTimeField | derived from events |
| `last_left_at` | DateTimeField | derived from events |
| `is_currently_present` | BooleanField | current attendance state |

#### `MeetingAttendanceEvent`
| Field | Type | Notes |
|-------|------|-------|
| `snapshot` | FK MeetingOwnerSnapshot | |
| `event_type` | CharField choices | `ARRIVAL / DEPARTURE` |
| `event_time` | DateTimeField | logged automatically when checkbox changes |
| `source` | CharField | manual / UI / import |
| `note` | CharField | optional operator note |

**Rule:** One owner may arrive, leave, and arrive again multiple times. Attendance during a vote is determined from the event timeline at the vote timestamp, not from a single pair of arrival/departure fields.

#### `VoteWeightStyle`
| Field | Type | Notes |
|-------|------|-------|
| `voting_method` | CharField choices | `BY_UNITS / BY_SHARE` |
| `weight_value` | DecimalField | normalized share / unit weight |
| `label` | CharField | text, letter, or number printed on ballot |
| `color` | CharField | ballot color |

**Rule:** Vote weight styles are reusable between meetings. If ownership structure changes and a new weight appears, the system adds a new style instead of rewriting old meeting snapshots.

#### `AgendaVoteSession`
| Field | Type | Notes |
|-------|------|-------|
| `agenda_item` | FK AgendaItem | |
| `started_at` | DateTimeField | voting start timestamp |
| `completed_at` | DateTimeField | voting save/finalize timestamp |
| `negative_form` | BooleanField | allows “kdo je proti?” workflow |
| `present_weight` | DecimalField | weight present at time of vote |
| `quorum_met` | BooleanField | whether the point could be voted |
| `result` | CharField choices | `APPROVED / REJECTED / DEFERRED / N/A` |

#### `AgendaVoteBallot`
| Field | Type | Notes |
|-------|------|-------|
| `session` | FK AgendaVoteSession | |
| `label` | CharField | copied from ballot type |
| `color` | CharField | copied from ballot type |
| `share_value` | DecimalField | weight represented by one ballot |
| `issued_count` | PositiveIntegerField | number of handed-out ballots of this type |
| `for_count` | PositiveIntegerField | |
| `against_count` | PositiveIntegerField | |
| `abstain_count` | PositiveIntegerField | |

**Rule:** If the operator enters any two of `for_count`, `against_count`, and `abstain_count`, the third value is auto-computed from `issued_count`.

#### `MeetingMinutes`
| Field | Type | Notes |
|-------|------|-------|
| `meeting` | OneToOne Meeting | |
| `content` | TextField | rich text / Markdown |
| `approved_by` | FK User | |
| `approved_at` | DateTimeField | |
| `cms_published` | BooleanField | whether to push to public CMS |
| `cms_published_at` | DateTimeField | |

#### `MeetingInvitation`
| Field | Type | Notes |
|-------|------|-------|
| `meeting` | FK Meeting | |
| `owner` | FK Owner | |
| `sent_at` | DateTimeField | |
| `delivery_method` | CharField choices | `EMAIL / POST / PERSONAL` |
| `confirmed` | BooleanField | |

### Workflow

#### 1. Preparation / planning

- User defines meeting title, date/time, location, and agenda items.
- Each agenda item stores its text, presenter, whether voting is required, the approval threshold, and the quorum needed for that point.
- User can generate invitation/announcement PDF and publish the invitation to the CMS.
- Agenda remains editable and reorderable while the meeting is still planned.

#### 2. Meeting start

- From the list of planned meetings, user chooses `Zahajit schuzi`.
- Start action freezes the owner list, ownership shares, and ballot type assignments into `MeetingOwnerSnapshot`.
- Meeting detail shows tabs:
    - `Obecne`
    - `Seznam vlastniku`
    - `Body schuze`
    - `Hlasovaci listky`

#### 3. Attendance / prezencni listina

- In `Seznam vlastniku`, user toggles owner presence with a checkbox.
- Every checkbox change creates a `MeetingAttendanceEvent` with the exact timestamp.
- Owner detail shows editable arrival/departure history.
- UI continuously shows:
    - current present share / unit weight
    - number of present owners
    - number of issued ballots
    - number of remaining ballots
    - whether the meeting is usnasenischopne

#### 4. Agenda management during meeting

- Agenda items may be reordered, edited, and new items may be inserted.
- Items already voted are visibly marked with the voting result.

#### 5. Voting

- Each votable agenda item has `Zacit hlasovat`.
- Voting form shows ballot types rather than individual owners.
- For each ballot type the UI displays the ballot label/color, represented share, issued ballot count, and inputs for `pro`, `proti`, `zdrzel se`.
- Entering any two counts auto-fills the third one.
- System computes totals in real time, including total weighted votes and threshold satisfaction.
- Negative-form voting is supported: operator records `proti` and `zdrzel se`, and `pro` is derived as the remainder.

#### 6. Export and closure

- Meeting export produces PDF with selected sections:
    - attendance sheet
    - voting details
    - agenda texts
    - general meeting information
- Minutes stay connected to the meeting record and may later be published to CMS.

### Dashboard Widget

- Upcoming meetings in the next 30 days.
- Last meeting status (open agenda items, unfinalized minutes, quorum state).
- Quick warning if a planned meeting has no generated invitation or no assigned ballot styles.

### Integrations

- Reads `FlatOwner` shares from `solomon_property` and freezes them at meeting start.
- Publishes minutes to `solomon_cms` when `MeetingMinutes.cms_published = True` (Phase 6).
- Publishes meeting invitation / announcement to `solomon_cms` during planning.

---

## Phase 2 (also) - DB Cleanup Script

Add management command `cleanup_netbox_leftovers` to `solomon_core`.

**What it cleans:**
- `ContentType` records for models from disabled/uninstalled NetBox apps (DCIM, IPAM, Virtualization, etc.) where `app_label` is not in `INSTALLED_APPS`.
- Stale `Permission` records orphaned from removed content types.
- Orphaned `LogEntry` (auditlog) records whose `content_type` no longer exists.
- Optionally: `ObjectChange` (NetBox change log) records for removed content types.

**Safety rules:**
- Dry-run mode by default: `--execute` flag required to actually delete.
- Prints a summary of what would be removed.
- Safe to re-run after every NetBox version upgrade.
- Never touches content types that belong to installed Solomon plugins.

```
docker compose exec netbox python manage.py cleanup_netbox_leftovers
docker compose exec netbox python manage.py cleanup_netbox_leftovers --execute
```

---

## Phase 3 - Technical Equipment Management (`solomon_equipment`)

### Purpose

Track all physical assets: main water/gas/heating valves, elevators, fire extinguishers, and any future equipment type. Per-device history of repairs, warranty, and end-of-life alerts.

### Models

#### `EquipmentCategory` (configurable)
User-managed list: valve, elevator, fire_extinguisher, pump, electrical_panel, ... No hardcoding.

| Field | Type |
|-------|------|
| `name` | CharField |
| `icon` | CharField (optional, CSS class) |
| `requires_serial` | BooleanField |
| `track_warranty` | BooleanField |
| `default_lifespan_years` | PositiveSmallIntegerField |

#### `Equipment`
| Field | Type | Notes |
|-------|------|-------|
| `category` | FK EquipmentCategory | |
| `name` | CharField | short descriptive name |
| `serial_number` | CharField | blank if not applicable |
| `model` | CharField | |
| `manufacturer` | CharField | |
| `building` | FK Building | |
| `floor` | SmallIntegerField | null = building-wide |
| `location_description` | CharField | "Kotelna, prava strana" |
| `status` | CharField choices | `ACTIVE / DECOMMISSIONED / OUT_OF_SERVICE` |
| `purchase_date` | DateField | |
| `installation_date` | DateField | |
| `warranty_until` | DateField | |
| `end_of_life_date` | DateField | |
| `note` | TextField | |

#### `EquipmentServiceEvent`
| Field | Type | Notes |
|-------|------|-------|
| `equipment` | FK Equipment | |
| `event_type` | CharField choices | `REPAIR / MAINTENANCE / REPLACEMENT / INSPECTION` |
| `date` | DateField | |
| `description` | TextField | |
| `performed_by` | FK Vendor (solomon_tenders, nullable) | or free text |
| `performed_by_name` | CharField | fallback free text |
| `cost` | DecimalField | |
| `attachments` | (use NetBox file attachment framework) | |

### Dashboard Widget

- Equipment count per category, per building.
- Items with `warranty_until` within 90 days (orange) / expired (red).
- Items with `end_of_life_date` within 180 days.

---

## Phase 3 - Equipment Inspection Manager (`solomon_inspection`)

### Purpose

Define repetitive inspection schedules per equipment item (or per category), track completions, attach reports, and alert on overdue/upcoming inspections.

### Relationship to `solomon_equipment`

`solomon_inspection` depends on (imports from) `solomon_equipment`. They are separate plugins but tightly coupled. Install order: equipment first, then inspection.

### Models

#### `InspectionType` (configurable)
| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField | e.g. "Rocni revize vyhradniho TZ", "Pozarni kontrola" |
| `equipment_category` | FK EquipmentCategory | null = applies to any |
| `legal_requirement` | BooleanField | e.g. mandatory by law |
| `authority` | CharField | who mandates it |

#### `InspectionSchedule`
| Field | Type | Notes |
|-------|------|-------|
| `equipment` | FK Equipment | |
| `inspection_type` | FK InspectionType | |
| `interval_months` | PositiveSmallIntegerField | recurrence |
| `last_inspection_date` | DateField | |
| `next_due_date` | DateField | computed: last + interval |
| `assigned_vendor` | FK Vendor (nullable) | |
| `active` | BooleanField | |

#### `Inspection`
| Field | Type | Notes |
|-------|------|-------|
| `schedule` | FK InspectionSchedule | |
| `date_performed` | DateField | |
| `result` | CharField choices | `PASSED / FAILED / CONDITIONAL / CANCELLED` |
| `inspector_name` | CharField | |
| `vendor` | FK Vendor (nullable) | |
| `report` | FileField | upload inspection report PDF |
| `notes` | TextField | |
| `follow_up_required` | BooleanField | |

**On save:** automatically updates `InspectionSchedule.last_inspection_date` and recalculates `next_due_date`.

### Dashboard Widget

- Overdue inspections (red).
- Inspections due in next 30 / 90 days (orange / yellow).
- Link to create new Inspection record.

---

## Phase 4 - Common Property Management (`solomon_commons`)

### Purpose

Catalog all shared spaces (laundry rooms, bike storage, cellars, gardens, service rooms). Track which spaces can be rented to residents and log rental agreements.

### Models

#### `CommonSpaceType` (configurable)
`name`: laundry room, bike storage, cellar corridor, garden area, parking space, storage unit, rooftop terrace, ...

#### `CommonSpace`
| Field | Type |
|-------|------|
| `space_type` | FK CommonSpaceType |
| `building` | FK Building |
| `identifier` | CharField ("Prace C1", "Kolo 04") |
| `floor` | SmallIntegerField |
| `area_m2` | DecimalField |
| `capacity` | PositiveSmallIntegerField |
| `rentable` | BooleanField |
| `description` | TextField |

#### `CommonSpaceRental`
| Field | Type | Notes |
|-------|------|-------|
| `space` | FK CommonSpace | |
| `tenant` | FK Person (solomon_property) | |
| `effective_from` | DateField | |
| `effective_to` | DateField | null = ongoing |
| `monthly_rent_czk` | DecimalField | |
| `deposit_czk` | DecimalField | |
| `note` | TextField | |

**Constraint:** One rentable space can have at most one active rental at a time (overlapping `effective_from/to` check).

---

## Phase 4 - Access Management (`solomon_access`)

### Purpose

Track who can access which buildings and common spaces. Manage physical keys and RFID/access cards including issuance, returns, and lost tags.

### Models

#### `AccessLevelType` (configurable)
`name`: resident, board member, contractor, cleaning staff, emergency, ...

#### `AccessTag`
| Field | Type | Notes |
|-------|------|-------|
| `tag_type` | CharField choices | `PHYSICAL_KEY / RFID_CARD / KEY_CODE / MAGNETIC_CARD` |
| `identifier` | CharField | key number, card serial |
| `owner` | FK Person (solomon_property) | |
| `buildings` | M2M Building | |
| `common_spaces` | M2M CommonSpace (solomon_commons) | |
| `issued_date` | DateField | |
| `returned_date` | DateField | null = still active |
| `lost` | BooleanField | |
| `deposit_paid_czk` | DecimalField | |
| `deposit_returned_czk` | DecimalField | |
| `note` | TextField | |

#### `BuildingAccess`
| Field | Type | Notes |
|-------|------|-------|
| `person` | FK Person | |
| `building` | FK Building | |
| `access_level` | FK AccessLevelType | |
| `from_date` | DateField | |
| `to_date` | DateField | null = ongoing |
| `granted_by` | FK User | |
| `note` | TextField | |

**Dashboard widget:** Access tags issued (count), unreturned keys, lost tags.

---

## Phase 4 - Energy Consumption Manager (`solomon_energy`)

### Purpose

Upload annual utility statements per energy type per scope (building / flat / common). Visualize consumption in charts: global, per building, per group of flats, per individual flat.

### Models

#### `EnergyType` (configurable)
`name`: cold water, hot water, heating, gas, electricity, ...  
`unit`: m3, kWh, GJ, ...  
`color_hex`: for chart segments

#### `EnergyStatement`
| Field | Type | Notes |
|-------|------|-------|
| `energy_type` | FK EnergyType | |
| `period_year` | PositiveSmallIntegerField | |
| `period_from` | DateField | |
| `period_to` | DateField | |
| `scope` | CharField choices | `BUILDING / FLAT / COMMON_SPACE` |
| `building` | FK Building | always set |
| `flat` | FK Flat (nullable) | if scope = FLAT |
| `common_space` | FK CommonSpace (nullable) | if scope = COMMON |
| `total_consumption` | DecimalField | |
| `total_cost_czk` | DecimalField | |
| `file_attachment` | FileField | original statement scan/PDF |
| `note` | TextField | |
| `uploaded_by` | FK User | |

**Charts (views, not stored):** Use aggregation queries + Chart.js or similar.  
- Global: sum per energy_type per year
- Per building: bar chart, year comparison
- Per flat: consumption over years
- Common spaces subtotal

**Upload flow:** Admin uploads PDF (stored as attachment) + manually enters total consumption/cost. Future: CSV import mapping.

---

## Phase 5 - Task / Issue Tracking (`solomon_tasks`)

### Purpose

Simplified issue tracker for the SVJ's own operational needs: repair requests, planned maintenance tasks, items from board meeting resolutions. Replaces email threads and paper lists.

### Models

#### `TaskCategory` (configurable)
`name`: repair, planned maintenance, board meeting task, owner request, ...  
`default_assignee_role`: (optional, for auto-assignment)

#### `Task`
| Field | Type | Notes |
|-------|------|-------|
| `category` | FK TaskCategory | |
| `title` | CharField | |
| `description` | TextField | |
| `status` | CharField choices | `OPEN / IN_PROGRESS / WAITING / RESOLVED / CLOSED` |
| `priority` | CharField choices | `LOW / NORMAL / HIGH / URGENT` |
| `building` | FK Building (nullable) | |
| `flat` | FK Flat (nullable) | |
| `reported_by` | FK User | |
| `assigned_to` | FK User (nullable) | |
| `due_date` | DateField | |
| `resolved_at` | DateTimeField | |
| `source` | CharField choices | `MANUAL / OWNER_REQUEST / MEETING_RESOLUTION` |
| `meeting_item` | FK AgendaItem (nullable) | if from meeting |

#### `TaskComment`
| Field | Type |
|-------|------|
| `task` | FK Task |
| `author` | FK User |
| `content` | TextField |
| `created_at` | DateTimeField |

**Exports:** CSV export, simple PDF report (filtered by status/category/date range).

**Dashboard widget:** Open tasks by priority. Overdue tasks (due_date < today, not resolved).

---

## Phase 5 - Tender Management (`solomon_tenders`)

### Purpose

Manage competitive bids for repairs, services, contracts. Maintain a registry of trusted vendors and craftsmen. Log all communications per tender.

### Models

#### `VendorSpecialty` (configurable)
`name`: plumbing, electrical, elevator maintenance, cleaning, landscaping, ...

#### `Vendor`
| Field | Type |
|-------|------|
| `name` | CharField |
| `vendor_type` | CharField choices | `COMPANY / INDIVIDUAL` |
| `ico` | CharField | Czech company ID |
| `address` | TextField | |
| `email` | CharField | |
| `phone` | CharField | |
| `specialties` | M2M VendorSpecialty | |
| `rating` | PositiveSmallIntegerField | 1-5, admin-assigned |
| `preferred` | BooleanField | |
| `blacklisted` | BooleanField | |
| `note` | TextField | |

#### `TenderCategory` (configurable)
`name`: roof repair, boiler replacement, garden maintenance, legal services, ...

#### `Tender`
| Field | Type | Notes |
|-------|------|-------|
| `title` | CharField | |
| `category` | FK TenderCategory | |
| `building` | FK Building (nullable) | |
| `description` | TextField | |
| `status` | CharField choices | `DRAFT / OPEN / EVALUATION / AWARDED / CANCELLED` |
| `deadline` | DateField | |
| `budget_czk` | DecimalField (nullable) | |
| `created_by` | FK User | |
| `awarded_to` | FK Vendor (nullable) | |
| `awarded_amount_czk` | DecimalField (nullable) | |

#### `TenderBid`
| Field | Type |
|-------|------|
| `tender` | FK Tender |
| `vendor` | FK Vendor |
| `amount_czk` | DecimalField |
| `submitted_at` | DateTimeField |
| `notes` | TextField |
| `attachment` | FileField |

#### `TenderCommunicationLog`
| Field | Type | Notes |
|-------|------|-------|
| `tender` | FK Tender | |
| `vendor` | FK Vendor (nullable) | |
| `date` | DateField | |
| `channel` | CharField choices | `EMAIL / PHONE / IN_PERSON / LETTER` |
| `summary` | TextField | |
| `recorded_by` | FK User | |

---

## Phase 6 - Public CMS (`solomon_cms`)

### Purpose

Publicly accessible web section (no login required) for mandatory SVJ disclosures, meeting notices, financial statements, general announcements, and newsletter sign-ups.

**Implementation:** Custom NetBox plugin with its own URL namespace (`/public/`). No standalone CMS service. Served by the same Django/Granian process.

### Models

#### `CMSPageCategory` (configurable)
`name`: annual_disclosure, meeting_notice, meeting_minutes, financial_statement, general_announcement, rules_and_regulations, ...

#### `CMSPage`
| Field | Type | Notes |
|-------|------|-------|
| `category` | FK CMSPageCategory | |
| `slug` | SlugField | URL-friendly |
| `title` | CharField | |
| `content` | TextField | Markdown |
| `published` | BooleanField | |
| `published_at` | DateTimeField | |
| `published_by` | FK User | |
| `building` | FK Building (nullable) | if building-specific |
| `pinned` | BooleanField | show at top |
| `attachments` | (NetBox file attachments) | for PDFs, statements |

#### `NewsletterSubscription`
| Field | Type | Notes |
|-------|------|-------|
| `email` | EmailField | |
| `confirmed` | BooleanField | double opt-in |
| `confirmation_token` | CharField | UUID, used in confirmation link |
| `subscribed_at` | DateTimeField | |
| `unsubscribed_at` | DateTimeField | |
| `building_filter` | FK Building (nullable) | subscribe to one building only |

**Public URLs (no auth):**
- `GET /public/` - homepage with pinned announcements
- `GET /public/page/<slug>/` - single page
- `GET /public/subscribe/` - newsletter form
- `GET /public/confirm/<token>/` - email confirmation
- `GET /public/unsubscribe/<token>/` - one-click unsubscribe

**Admin URLs (auth required):**  
Standard NetBox plugin CRUD.

**Integration with `solomon_meetings`:**  
When `MeetingMinutes.cms_published = True`, a `CMSPage` is auto-created in category `meeting_minutes` with the minutes content.

---

## Phase 7 - Commercial / SaaS (`solomon_saas`)

### Purpose

Enable Solomon to be sold as a multi-tenant SaaS product to other SVJ communities. Includes plugin marketplace, license management, payments, and self-service activation.

### Scope Decision

This is a **separate commercial layer**. The SVJ-facing feature plugins (Phases 2-6) work independently of this. `solomon_saas` only becomes relevant when deploying Solomon for new paying customers.

### Sub-components

#### Plugin Marketplace
- Installable module list with descriptions, screenshots, pricing tier.
- Activation/deactivation per license.

#### License Management
| Model | Key Fields |
|-------|-----------|
| `License` | key, plan (STARTER/PRO/ENTERPRISE), valid_from, valid_to, max_buildings, features[] |
| `LicenseFeature` | flag name, enabled by this plan |
| `Organization` | tenant identifier, linked License |

#### Payment Integration
- Stripe or GoPay (Czech payment gateway) integration.
- `Payment` model: amount, currency, date, method, status, license FK.
- Webhook handler for payment confirmation.

#### Self-app plugins
| Plugin | Purpose |
|--------|---------|
| `solomon_backup` | UI to trigger/schedule PostgreSQL dumps, download, restore |
| `solomon_support` | In-app bug report form, sends to email + optionally creates GitHub issue |
| Contact info page | Sales/technical contact displayed in sidebar footer |

---

## SVJ vs. Housing Cooperative (BD) - Architecture

### Differences

| Aspect | SVJ (default) | BD (future) |
|--------|--------------|-------------|
| Ownership | Direct property share (FlatOwner) | Cooperative membership share |
| Ownership document | List vlastnictvi (LV) | Clenska knizka / podil |
| Voting weight | Ownership share % | Membership units |
| Meeting type | Shromazdeni vlastniku | Clenska schuze |
| Legal basis | Civil Code s. 1208+ | Zakon o obchodnich korporacich |

### Design Approach

1. Add `organization_type` field to a future `SVJProfile` or `OrganizationConfig` model (singleton):  `CHOICES = [("SVJ", "Spolecenstvi vlastniku"), ("BD", "Bytove druzstvo")]`
2. `FlatOwner.share_numerator/denominator` stays - it maps to LV share for SVJ and membership fraction for BD.
3. All voting methods in `AgendaItem` already support both BY_UNITS and BY_SHARE.
4. Template labels adapt based on `organization_type` (e.g. "Shromazdeni" vs "Clenska schuze").
5. No forking of models - conditional display + adapted labels.
6. BD-specific fields (membership ID, cooperative entry fee) added to `Owner` as nullable fields, only shown when BD mode is active.

**This requires no breaking changes to Phase 2-5 designs.** BD support is a configuration flag + label/field additions.

---

## Plugin Dependency Graph

```
solomon_core  (foundation, always installed)
    |
    +-- solomon_property  (buildings, flats, owners, tenants)
            |
            +-- solomon_meetings  (reads FlatOwner shares)
            +-- solomon_commons   (reads Building, Person)
            +-- solomon_access    (reads Building, Person, CommonSpace)
            +-- solomon_energy    (reads Building, Flat, CommonSpace)
            +-- solomon_tasks     (reads Building, Flat; optionally AgendaItem)
            |
            +-- solomon_equipment (reads Building)
                    |
                    +-- solomon_inspection (reads Equipment, EquipmentCategory)
                    +-- solomon_tenders    (Vendor used in ServiceEvent)

solomon_cms
    |
    +-- reads MeetingMinutes from solomon_meetings (optional, soft dependency)

solomon_saas  (standalone, wraps everything)
```

---

## Implementation Notes Per Plugin

### File structure (same for every new plugin)
```
plugins/solomon_<name>/
    pyproject.toml
    solomon_<name>/
        __init__.py             # PluginConfig
        models.py
        views.py
        forms.py
        tables.py
        filtersets.py
        filterforms.py
        navigation.py
        urls.py
        api/
            __init__.py
            serializers.py
            urls.py
            views.py
        migrations/
            __init__.py
        templates/
            solomon_<name>/
                <model>_list.html
                <model>.html
                <model>_edit.html
        tests/
            __init__.py
            test_models.py
            test_views.py
```

### Registration
Each new plugin must be added to `docker/configuration/plugins.py` PLUGINS list, and a `module_map` entry added to `solomon_core/module_map.py` if it has a sidebar menu section.

### Migrations
```bash
docker compose exec netbox python manage.py makemigrations solomon_<name>
docker compose exec netbox python manage.py migrate solomon_<name>
```

---

## Open Questions (deferred, not blocking)

| Question | Context | Reply |
|----------|---------|-------|
| Meeting invitation delivery | Email only, or also support postal/SMS? Needs email configuration. | Publish via CMS plugin|
| Energy CSV import format | Which utility company formats should be supported for bulk upload? | |
| GDPR retention for newsletter | How long should unsubscribed emails be retained? | Delete imidiatelly |
| CMS URL / subdomain | Will `/public/` path be enough, or does it need its own subdomain (e.g. `www.bdsalounova.cz`)? Reverse proxy needed if subdomain. | /public is enough, link from main site |
| Payment gateway for SaaS | Stripe (international) or GoPay (Czech)? | No payment gateway for now. Offline payment to account by transfer for now |
| Multi-tenancy for SaaS | Single-instance with `Organization` FK everywhere, or separate DB per tenant? | One instance of app will be dedicated to one customer. |
| Meeting minutes format | Plain text Markdown editor, or rich text (Quill/TipTap)? | Rich text editor |
