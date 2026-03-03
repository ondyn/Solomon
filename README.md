# Solomon# Solomon — Facility Management System (BD Salounova)# Solomon — Facility Management System (BD Salounova)# Facility Management System — BD Salounova# Facility Management System



Facility Management System for BD Salounova — managing apartment buildings under SVJ in the Czech Republic.



## Documentation## Software Design Document



- [Software Design Document](DESIGN.md) — full system architecture, data model, technology stack



## Tech Stack---## Software Design Document



- **Backend:** Django (Python)

- **Frontend:** Django Templates + HTMX

- **Database:** PostgreSQL## 1. Introduction

- **Hosting:** Fly.io (MVP) / Czech VPS (production)



## Repository

### 1.1 Purpose---## Software Design Document## Software Design Document

- GitHub: [ondyn/Solomon](https://github.com/ondyn/Solomon)

- Website: [bdsalounova.cz](https://www.bdsalounova.cz/)A facility management system designed for managing residential property — specifically a row of interconnected apartment buildings (house of flats) operated under a single legal entity (SVJ or Housing Cooperative) in the Czech Republic. The system replaces existing manual processes used by the property manager.




### 1.2 Scope

Users will be able to handle all tasks related to managing their property: building and flat registry, owner and tenant management, financial tracking, utility management, maintenance and repairs, communication, meetings, and document management. The system is designed as a set of **independent modules** that can be designed and implemented incrementally.## 1. Introduction1. ### Introduction



### 1.3 MVP Scope (Phase 1)

- **Building management** — CRUD operations for buildings and their parameters

- **Flat management** — CRUD operations for flats/units and their parameters### 1.1 Purpose---- Purpose: Facility management system

- **Owner management** — CRUD operations for owners (natural or legal persons), including co-ownership

- **Tenant management** — CRUD operations for tenants, linked to flats and ownersA facility management system designed for managing residential property — specifically a row of interconnected apartment buildings (house of flats) operated under a single legal entity (SVJ or Housing Cooperative) in the Czech Republic. The system replaces existing manual processes and spreadsheets used by the property manager.

- **Full audit trail** — Every change is recorded: who made it, when, what changed, and the effective date

- Scope: Users will be able to handle all tasks related to manage their property. Usually house of flats and all related tasks.

### 1.4 Future Modules (Phase 2+)

- **Financial Management** — fee collection, expense tracking, cost per project/repair/service### 1.2 Scope

- **Utility Management** — meter readings, utility cost calculations per flat

- **Maintenance & Repairs** — repair requests, status tracking, scheduling, contractor managementUsers will be able to handle all tasks related to managing their property: building and flat registry, owner and tenant management, financial tracking, utility management, maintenance and repairs, communication, meetings, and document management. The system is designed as a set of **independent modules** that can be designed and implemented incrementally.## 1. Introduction- Definitions and Acronyms: 

- **Communication** — internal announcements, notifications (external website at https://www.bdsalounova.cz/)

- **Meetings & Voting** — meeting planning, minutes, resolutions, quorum tracking

- **Document Management** — contracts, certificates, house rules, meeting minutes

### 1.3 MVP Scope (Phase 1)    - Flat: The building contains several apartments (flats) with different parameters (area, number of rooms, number of water and waste outlets, number of radiators and their power, whether gas is installed, etc.) 

### 1.5 Definitions and Acronyms

The first version of the system focuses on the **core property registry**:

| Term | Definition |

|------|-----------|- **Building management** — CRUD operations for buildings and their parameters### 1.1 Purpose    - Building: Building contains flats and has its own parameters as floor plan, common rooms (such as laundry room, drying room, bike room, workshop), address, descriptive and indicative number, 

| **Flat (Jednotka)** | An apartment unit within a building. Parameters: area, rooms, layout, floor, water/waste outlets, radiators and power, gas, balcony, cellar unit, ownership certificate number. |

| **Building (Budova)** | A physical structure containing flats. Parameters: address, descriptive/indicative number, floor plan, common rooms, floors, elevator, year built, total units, land plot number, common area rental. |- **Flat management** — CRUD operations for flats/units and their parameters

| **Owner (Vlastník)** | A natural or legal person who owns a flat (SVJ) or holds a cooperative share. One owner can own multiple flats. One flat can have multiple owners (co-ownership). |

| **Tenant (Nájemník)** | A person renting a flat from its owner. One flat can have multiple tenants. |- **Owner management** — CRUD operations for owners (natural or legal persons), including co-ownershipA facility management system designed for managing residential property — specifically a row of interconnected apartment buildings (house of flats) operated under a single legal entity (SVJ or Housing Cooperative) in the Czech Republic. The system replaces existing manual processes and spreadsheets used by the property manager.    - Owner: Unit which owns the flat (Association of Unit Owners) or have the right to use the flat (housing cooperative)

| **SVJ (Společenství vlastníků jednotek)** | Association of Unit Owners. Primary legal model for this system. |

| **Housing Cooperative (Bytové družstvo)** | Alternative legal model. Members don't own apartments directly but have a cooperative share. |- **Tenant management** — CRUD operations for tenants, linked to flats and owners

| **Administrator (Správce)** | Single property manager for all buildings. Full read/write access. |

| **Board Member (Člen výboru)** | SVJ board member (5 total). Full read/write access. Can approve expenses and repairs. |- **Full audit trail** — Every change is recorded: who made it, when, what changed, and the effective date (since when it applies)    - Housing cooperative: A housing cooperative is a legal entity and a specific business corporation, established by at least 3 members primarily for the purpose of providing housing needs of its members, not for the purpose of doing business. It owns an apartment building and concludes lease agreements with its members for an indefinite period; members do not own the apartments directly, but have a cooperative share.

| **Chairman (Předseda)** | Head of board. All board permissions + approval of contracts above threshold. |

| **Individual Owner (Vlastník – uživatel)** | Read-only access to own data. Can submit requests but cannot edit directly. |

| **Audit Trail** | Complete history log: timestamp, who, what changed (old → new), effective date. |

| **Effective Date (Platnost od)** | Real-world date from which a change applies, vs. when it was recorded. |### 1.4 Future Modules (Phase 2+)### 1.2 Scope    - Association of Unit Owners: Unit Owners Association. This is a legal entity established for the purpose of managing, operating and repairing common parts of a house and land. All owners of apartments and non-residential premises in a given house are mandatory members of the SVJ.



---The following modules are defined conceptually but will be designed and implemented later:



## 2. System Overview- **Financial Management** — fee collection, expense tracking, cost per project/repair/serviceUsers will be able to handle all tasks related to managing their property: building and flat registry, owner and tenant management, financial tracking, utility management, maintenance and repairs, communication, meetings, and document management. The system is designed as a set of **independent modules** that can be designed and implemented incrementally.



### 2.1 System Description- **Utility Management** — meter readings, utility cost calculations per flat

Solomon is a **web-based application** for managing a residential property complex of 5 interconnected apartment buildings operated under a single SVJ in the Czech Republic. It serves as the central tool for the property administrator, board members, and individual owners.

- **Maintenance & Repairs** — repair requests, status tracking, scheduling, contractor management1. ### System Overview

### 2.2 User Personas

- **Communication** — internal announcements, notifications (external website exists at https://www.bdsalounova.cz/)

**Administrator (Správce)** — Single property manager. Full CRUD on all data. Typical tasks: register owners, update flats, manage repairs.

- **Meetings & Voting** — meeting planning, minutes, resolutions, quorum tracking### 1.3 MVP Scope (Phase 1)- System Description

**Chairman (Předseda)** — Head of 5-member board. Full access + special approvals (contracts above threshold).

- **Document Management** — contracts, certificates, house rules, meeting minutes

**Board Member (Člen výboru)** — Full read/write. Can approve expenses and repair requests.

The first version of the system focuses on the **core property registry**:1. ### Architectural Design

**Individual Owner (Vlastník)** — Read-only on own data. Can submit change/repair requests.

### 1.5 Definitions and Acronyms

### 2.3 Modular Architecture

- **Building management** — CRUD operations for buildings and their parameters- System Architecture Diagram

```

┌─────────────────────────────────────────────────────────────┐| Term | Definition |

│                          SOLOMON                             │

├─────────────────────────────────────────────────────────────┤|------|-----------|- **Flat management** — CRUD operations for flats/units and their parameters- Component Breakdown

│  MVP:  🏗 Building │ 🏠 Flat │ 👤 Owner │ 🧑 Tenant │ 📋 Audit │

├─────────────────────────────────────────────────────────────┤| **Flat (Jednotka)** | An apartment unit within a building. Has parameters: area, number of rooms, layout, floor number, number of water and waste outlets, number of radiators and their power, gas installation status, balcony, cellar unit, unit ownership certificate number. |

│  Future: 💰 Finance │ 🔧 Utility │ 🛠 Repairs │ 📢 Comms  │

│          🗳 Meetings │ 📄 Documents                         │| **Building (Budova)** | A physical structure containing flats. Has parameters: address, descriptive number (číslo popisné), indicative number (číslo orientační), floor plan, common rooms (laundry, drying room, bike room, workshop), number of floors, elevator, year built, total units, land plot number, rental of common areas. |- **Owner management** — CRUD operations for owners (natural or legal persons), including co-ownership- Technology Stack

├─────────────────────────────────────────────────────────────┤

│  🔐 Auth & Roles │ 🌍 Localization (CZ) │ 📝 Audit Engine │| **Owner (Vlastník)** | A natural or legal person who owns a flat (in SVJ) or holds a cooperative share (in housing cooperative). One owner can own multiple flats. One flat can be owned by multiple owners (co-ownership). |

└─────────────────────────────────────────────────────────────┘

```| **Tenant (Nájemník)** | A person renting a flat from its owner. One flat can have multiple tenants. The system tracks their contact information. |- **Tenant management** — CRUD operations for tenants, linked to flats and owners- Data Flow and Control Flow



### 2.4 Key Characteristics| **SVJ (Společenství vlastníků jednotek)** | Association of Unit Owners. A legal entity established for managing, operating and repairing common parts of a house and land. All owners of apartments and non-residential premises are mandatory members. This is the primary legal model for this system. |

- **Multi-building:** 5 buildings under one SVJ

- **Single management:** One administrator, one board (5 members + chairman)| **Housing Cooperative (Bytové družstvo)** | A legal entity and specific business corporation, established by at least 3 members primarily for providing housing needs. It owns the apartment building and concludes lease agreements with members; members do not own apartments directly but have a cooperative share. Supported as an alternative legal model. |- **Full audit trail** — Every change is recorded: who made it, when, what changed, and the effective date (since when it applies)

- **Multi-language:** Czech primary, localization-ready

- **Full audit trail:** Every change tracked with user, timestamp, diff, effective date| **Administrator (Správce)** | The property manager responsible for the day-to-day operation of all buildings. There is one administrator for the entire property. Has full read/write access to all data. |

- **Role-based access:** 4 roles with different permissions

- **Modular:** Independent modules built incrementally| **Board Member (Člen výboru)** | A member of the SVJ/cooperative governing board (5 members total). Has full read/write access. Can approve expenses and repair requests. |1. ### Detailed Design

- **Czech legal context:** SVJ primary, housing cooperative alternative

| **Chairman (Předseda)** | The head of the board. Has all board member permissions plus special approval rights: approving repair requests, contracts above a defined monetary threshold. |

---

| **Individual Owner (Vlastník – uživatel)** | An owner accessing the system. Can view only their own relevant data (their flats, their financial records, their utility readings). Can submit requests (repair, data change) but cannot edit data directly. |### 1.4 Future Modules (Phase 2+)- [Component Name]

## 3. Architectural Design

| **Audit Trail** | A complete history log of every data change: timestamp of change, who performed it, what field changed (old value → new value), and the effective date (since when the change applies in the real world). |

### 3.1 Foundation Layer

| Component | Responsibility || **Effective Date (Platnost od)** | The real-world date from which a change applies (e.g., ownership transfer date), as opposed to the timestamp when the change was recorded in the system. |The following modules are defined conceptually but will be designed and implemented later:    - Responsibilities: [What does it do?]

|-----------|---------------|

| **Auth & Identity** | Login, session management, role assignment |

| **Authorization Engine** | Permission checks by role and data ownership |

| **Audit Trail Engine** | Records all changes: user, timestamp, entity, field, old/new value, effective date |---- **Financial Management** — fee collection, expense tracking, cost per project/repair/service    - Interfaces/APIs:

| **Localization Service** | Translations, Czech date/currency/number formatting |

| **Notification Engine** | In-app + email notifications |



### 3.2 MVP Modules## 2. System Overview- **Utility Management** — meter readings, utility cost calculations per flat    - Inputs: [Describe input data.]



**Building Management (Správa budov)** — CRUD for buildings and parameters. Soft delete. Audit trail on all changes.



**Flat Management (Správa jednotek)** — CRUD for flats. Each flat belongs to one building. Supports multiple owners and tenants.### 2.1 System Description- **Maintenance & Repairs** — repair requests, status tracking, scheduling, contractor management    - Outputs: [Describe output data.]



**Owner Management (Správa vlastníků)** — CRUD for owners (natural/legal persons). M:N with flats via ownership shares. Effective dates required.Solomon is a **web-based application** for managing a residential property complex consisting of 5 interconnected apartment buildings operated under a single SVJ (Společenství vlastníků jednotek) in the Czech Republic.



**Tenant Management (Správa nájemníků)** — CRUD for tenants linked to flats. Multiple tenants per flat. Soft delete on move-out.- **Communication** — internal announcements, notifications (external website exists at https://www.bdsalounova.cz/)    - Error Handling: [Describe approach.]



**Audit Trail (Historie změn)** — Immutable log. Two dates: system timestamp + effective date. Filterable. Transactional (if logging fails, operation fails).The system serves as the central tool for the property administrator, board members, and individual owners to manage all aspects of the property — from the physical registry of buildings and flats, through ownership and tenancy records, to financial tracking, maintenance, and communication.



### 3.3 Data Flow- **Meetings & Voting** — meeting planning, minutes, resolutions, quorum tracking    - Data Structures: [Key models/schemas.]



```### 2.2 User Personas

Owner (view/request) ──► Application ◄──► Auth & Authorization

Admin/Board (CRUD)   ──► Layer       ──► Audit Trail Engine- **Document Management** — contracts, certificates, house rules, meeting minutes    - Algorithms/Logic: [Design patterns or important logic.]

Chairman (approve)   ──►    │        ──► Notification Engine

                            ▼#### Persona 1: Administrator (Správce)

                        Database

```- **Who:** The single property manager responsible for all 5 buildings    - State Management: [How is state handled?]



---- **Goals:** Maintain accurate records of all buildings, flats, owners, and tenants. Track finances, coordinate repairs, manage utilities.



## 4. Detailed Design- **Access level:** Full read/write access to all data across all buildings and modules### 1.5 Definitions and Acronyms



### 4.1 Building Management- **Typical tasks:** Register new owner, update flat parameters, record meter readings, generate financial reports, manage repair requests

| Inputs | Building data (address, parameters), user identity |

|--------|-----|1. ### Database Design

| **Outputs** | Building records, filtered by role, change history |

| **Validation** | Required: address, descriptive number. Cannot delete building with active flats. |#### Persona 2: Chairman (Předseda)

| **Rules** | Soft delete only. All changes produce audit trail entries. |

- **Who:** Head of the 5-member SVJ board| Term | Definition |ER Diagram / Schema Diagram:

### 4.2 Flat Management

| Inputs | Flat data (area, rooms, layout, etc.), building reference |- **Goals:** Oversee property management, approve significant decisions

|--------|-----|

| **Outputs** | Flat records per building, owners/tenants per flat, history |- **Access level:** Full read/write access + special approval rights (repair requests, contracts above defined threshold)|------|-----------|Use Mermaid ER diagram here.

| **Validation** | Area > 0. Floor ≤ building floors. Required fields. |

| **Rules** | Belongs to one building. Co-ownership via M:N. Soft delete. |- **Typical tasks:** Approve large expenses, review repair requests, sign off on contracts, oversee board decisions



### 4.3 Owner Management| **Flat (Jednotka)** | An apartment unit within a building. Has parameters: area, number of rooms, layout, floor number, number of water and waste outlets, number of radiators and their power, gas installation status, balcony, cellar unit, unit ownership certificate number. |Tables/Collections: [Define each with fields and constraints.]

| Inputs | Owner data (name, type, contacts, deputy, share), flat references, effective dates |

|--------|-----|#### Persona 3: Board Member (Člen výboru)

| **Outputs** | Owner records, owned flats, ownership history |

| **Validation** | Share sizes should sum to 100% per flat (warning). Required contacts. |- **Who:** One of 5 members of the SVJ governing board| **Building (Budova)** | A physical structure containing flats. Has parameters: address, descriptive number (číslo popisné), indicative number (číslo orientační), floor plan, common rooms (laundry, drying room, bike room, workshop), number of floors, elevator, year built, total units, land plot number, rental of common areas. |Relationships: [Describe relationships between entities.]

| **Rules** | Natural or legal person. Deputy supported. Effective date required on changes. |

- **Goals:** Participate in property management decisions, review data

### 4.4 Tenant Management

| Inputs | Tenant data (name, contacts), flat reference, lease dates |- **Access level:** Full read/write access, can approve expenses and repair requests| **Owner (Vlastník)** | A natural or legal person who owns a flat (in SVJ) or holds a cooperative share (in housing cooperative). One owner can own multiple flats. One flat can be owned by multiple owners (co-ownership). |Migration Strategy: [If applicable.]

|--------|-----|

| **Outputs** | Tenant records per flat, lease history |- **Typical tasks:** Review financial reports, approve repair requests, update property data

| **Validation** | Lease start < end. Warn on overlapping tenancies. |

| **Rules** | Multiple per flat. Linked to flat, not owner. Move-out = soft delete. || **Tenant (Nájemník)** | A person renting a flat from its owner. One flat can have multiple tenants. The system tracks their contact information. |1. ### External Interfaces



### 4.5 Audit Trail#### Persona 4: Individual Owner (Vlastník)

| Inputs | Automatic on every create/update/delete |

|--------|-----|- **Who:** An owner of one or more flats| **SVJ (Společenství vlastníků jednotek)** | Association of Unit Owners. A legal entity established for managing, operating and repairing common parts of a house and land. All owners of apartments and non-residential premises are mandatory members. This is the primary legal model for this system. |User Interface: [Mockups, UX notes.]

| **Outputs** | Chronological log per entity/user/global. Filterable, exportable. |

| **Rules** | Immutable. System timestamp + effective date. Transactional with operations. |- **Goals:** View their own data, submit requests



---- **Access level:** Read-only access to their own relevant data (their flats, their financial records). Can submit change requests and repair requests but cannot edit data directly.| **Housing Cooperative (Bytové družstvo)** | A legal entity and specific business corporation, established by at least 3 members primarily for providing housing needs. It owns the apartment building and concludes lease agreements with members; members do not own apartments directly but have a cooperative share. Supported as an alternative legal model. |External APIs: [Integrations and dependencies.]



## 5. Database Design- **Typical tasks:** View their flat details, check utility costs, submit a repair request, request a data change (e.g., new phone number — but the change must be confirmed by admin/board)



### 5.1 ER Diagram| **Administrator (Správce)** | The property manager responsible for the day-to-day operation of all buildings. There is one administrator for the entire property. Has full read/write access to all data. |Hardware Interfaces: [If any.]



```mermaid### 2.3 Modular Architecture (Conceptual)

erDiagram

    BUILDING ||--o{ FLAT : containsThe system is composed of independent modules. Each module can be designed, implemented, and deployed separately. All modules share a common foundation.| **Board Member (Člen výboru)** | A member of the SVJ/cooperative governing board (5 members total). Has full read/write access. Can approve expenses and repair requests. |Network Protocols/Communication:

    FLAT ||--o{ FLAT_OWNER : "owned by"

    OWNER ||--o{ FLAT_OWNER : owns

    FLAT ||--o{ TENANT : "rented by"

    USER ||--o{ AUDIT_LOG : performs```| **Chairman (Předseda)** | The head of the board. Has all board member permissions plus special approval rights: approving repair requests, contracts above a defined monetary threshold. |[REST, GraphQL, gRPC, WebSockets, etc.]



    BUILDING {┌─────────────────────────────────────────────────────────────────────┐

        UUID id PK

        string address│                              SOLOMON                                │| **Individual Owner (Vlastník – uživatel)** | An owner accessing the system. Can view only their own relevant data (their flats, their financial records, their utility readings). Can submit requests (repair, data change) but cannot edit data directly. |1. ### Security Considerations

        string descriptive_number

        string indicative_number│                     Facility Management System                      │

        int number_of_floors

        boolean elevator├─────────────────────────────────────────────────────────────────────┤| **Audit Trail** | A complete history log of every data change: timestamp of change, who performed it, what field changed (old value → new value), and the effective date (since when the change applies in the real world). |Authentication: [Method used.]

        int year_built

        int total_units│                                                                     │

        string land_plot_number

        text common_rooms│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │| **Effective Date (Platnost od)** | The real-world date from which a change applies (e.g., ownership transfer date), as opposed to the timestamp when the change was recorded in the system. |Authorization: [Role/permission models.]

        string floor_plan_url

        text common_area_rental│  │  🏗 Building  │  │  🏠 Flat     │  │  👤 Owner    │  MVP        │

        text notes

        boolean is_deleted│  │  Management  │  │  Management  │  │  Management  │  (Phase 1)  │Data Protection: [Encryption, storage.]

    }

│  └──────────────┘  └──────────────┘  └──────────────┘              │

    FLAT {

        UUID id PK│  ┌──────────────┐  ┌──────────────┐                                │---Compliance: [GDPR, HIPAA, etc.]

        UUID building_id FK

        string unit_number│  │  🧑 Tenant   │  │  📋 Audit    │                  MVP          │

        decimal area_sqm

        int number_of_rooms│  │  Management  │  │  Trail       │                  (Phase 1)    │Threat Model:

        string layout

        int floor_number│  └──────────────┘  └──────────────┘                                │

        int water_outlets

        int waste_outlets│                                                                     │## 2. System OverviewUse Mermaid diagram here if helpful.

        int radiator_count

        decimal radiator_power_kw│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

        boolean gas_installed

        boolean has_balcony│  │  💰 Financial│  │  🔧 Utility  │  │  🛠 Mainten. │  Future     │1. ### Performance and Scalability

        string cellar_unit

        string ownership_certificate_number│  │  Management  │  │  Management  │  │  & Repairs   │  (Phase 2+) │

    }

│  └──────────────┘  └──────────────┘  └──────────────┘              │### 2.1 System DescriptionExpected Load: [Requests per second, data volume.]

    OWNER {

        UUID id PK│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

        enum person_type "natural/legal"

        string name│  │  📢 Communi- │  │  🗳 Meetings │  │  📄 Document │  Future     │The Facility Management System is a **web-based application** for managing a residential property complex consisting of 5 interconnected apartment buildings operated under a single SVJ (Společenství vlastníků jednotek) in the Czech Republic.Caching Strategy: [Describe caches used.]

        string permanent_address

        string contact_address│  │  cation      │  │  & Voting    │  │  Management  │  (Phase 2+) │

        string phone

        string email│  └──────────────┘  └──────────────┘  └──────────────┘              │Database Optimization: [Indexes, partitioning.]

        string deputy_name

        string deputy_contact│                                                                     │

        date move_in_date

        text notes├─────────────────────────────────────────────────────────────────────┤The system serves as the central tool for the property administrator, board members, and individual owners to manage all aspects of the property — from the physical registry of buildings and flats, through ownership and tenancy records, to financial tracking, maintenance, and communication.Scaling Strategy: [Vertical/horizontal.]

        boolean is_deleted

    }│  🔐 Authentication & Authorization │ 🌍 Localization (CZ primary) │



    FLAT_OWNER {│  📝 Audit Trail Engine             │ 🔔 Notification Engine        │1. ### Deployment Architecture

        UUID id PK

        UUID flat_id FK├─────────────────────────────────────────────────────────────────────┤

        UUID owner_id FK

        int share_numerator│                    Shared Foundation / Common Services               │### 2.2 User PersonasEnvironments: [Dev, staging, production.]

        int share_denominator

        date effective_from└─────────────────────────────────────────────────────────────────────┘

        date effective_to

    }```CI/CD Pipeline: [Tools and stages.]



    TENANT {

        UUID id PK

        UUID flat_id FK### 2.4 Key System Characteristics#### Persona 1: Administrator (Správce)Infrastructure Diagram:

        string name

        string permanent_address- **Multi-building:** Supports 5 buildings under one SVJ, extensible

        string contact_address

        string phone- **Single management entity:** One administrator, one board (5 members + chairman)- **Who:** The single property manager responsible for all 5 buildingsUse Mermaid diagram here.

        string email

        date lease_start- **Multi-language:** Localization support with Czech as the primary language

        date lease_end

        boolean is_deleted- **Full audit trail:** Every data change is tracked with user, timestamp, diff, and effective date- **Goals:** Maintain accurate records of all buildings, flats, owners, and tenants. Track finances, coordinate repairs, manage utilities.Cloud/Hosting: [AWS, GCP, Azure, etc.]

    }

- **Role-based access:** Four distinct roles with different permissions

    USER {

        UUID id PK- **Modular:** Independent modules that can be built incrementally- **Access level:** Full read/write access to all data across all buildings and modulesContainerization/Orchestration: [Docker, Kubernetes.]

        UUID owner_id FK "nullable"

        string username- **Czech legal context:** Designed for SVJ (primary) with housing cooperative as alternative

        enum role "admin/chairman/board/owner"

        string language_preference- **Typical tasks:** Register new owner, update flat parameters, record meter readings, generate financial reports, manage repair requests10. Testing Strategy

        boolean is_active

    }---



    AUDIT_LOG {Unit Testing: [Tools, coverage goals.]

        UUID id PK

        UUID user_id FK## 3. Architectural Design

        string entity_type

        UUID entity_id#### Persona 2: Chairman (Předseda)Integration Testing: [Approach and tools.]

        enum action "create/update/delete"

        string field_name### 3.1 Technology Stack

        text old_value

        text new_value- **Who:** Head of the 5-member SVJ boardEnd-to-End Testing: [Scope and tools.]

        date effective_date

        datetime recorded_at#### 3.1.1 Recommendation: Django (Python) — Full-Stack Monolith

    }

```- **Goals:** Oversee property management, approve significant decisionsQuality Metrics: [Code coverage, linting, etc.]



### 5.2 Key RelationshipsAfter analyzing the project requirements, the recommended technology stack is:

| Relationship | Type | Description |

|-------------|------|-------------|- **Access level:** Full read/write access + special approval rights (repair requests, contracts above defined threshold)11. Appendices

| Building → Flat | 1:N | Building contains many flats |

| Flat ↔ Owner | M:N | Via FLAT_OWNER with share size and effective dates || Layer | Technology | Rationale |

| Flat → Tenant | 1:N | Flat can have multiple tenants |

| User → Owner | 1:1 optional | Owner may have a user account ||-------|-----------|-----------|- **Typical tasks:** Approve large expenses, review repair requests, sign off on contracts, oversee board decisionsDiagrams: [All referenced diagrams.]

| User → Audit Log | 1:N | Every action logged |

| **Backend + Frontend** | **Django** (Python) | Full-stack web framework with built-in admin, ORM, auth, localization, and audit capabilities. Perfect for data-driven CRUD applications. |

### 5.3 Design Principles

- **Soft deletes** — `is_deleted` flag, never hard delete| **Database** | **PostgreSQL** | Robust relational database. Required for M:N relationships, temporal data, audit trail. Free on most hosting. |Glossary: [Terms and definitions.]

- **Temporal data** — `effective_from` / `effective_to` dates

- **Immutable audit log** — append-only| **Frontend Enhancement** | **Django Templates + HTMX** | Server-rendered HTML with HTMX for dynamic interactions without JavaScript complexity. Clean, fast, maintainable. |

- **UUID primary keys** — no sequential IDs exposed

| **CSS Framework** | **Tailwind CSS** or **Bootstrap 5** | Responsive design out of the box. No designer needed. |#### Persona 3: Board Member (Člen výboru)Change History:

---

| **Localization** | **Django i18n** (built-in) | Django has first-class internationalization support. Czech translations built-in. |

## 6. Technology Stack

| **Audit Trail** | **django-auditlog** or **django-simple-history** | Mature packages that automatically track all model changes with user, timestamp, old/new values. |- **Who:** One of 5 members of the SVJ governing board[Version, Date, Author, Changes]

### 6.1 Decision: Django + HTMX + PostgreSQL

- **Goals:** Participate in property management decisions, review data

After analyzing the requirements (small-scale web app, ~200 users, CRUD-heavy, audit trail, role-based access, Czech localization, needs free/cheap hosting), the recommended stack is:

#### 3.1.2 Why Django over React.js?- **Access level:** Full read/write access, can approve expenses and repair requests

#### Backend: Django (Python)

**Why Django over alternatives:**- **Typical tasks:** Review financial reports, approve repair requests, update property data

- **Built-in admin panel** — instant CRUD interface for all models, huge time saver for MVP

- **Built-in auth & permissions** — user management, groups, role-based access out of the box| Criteria | Django (recommended) | React.js + API backend |

- **Built-in i18n/l10n** — Czech localization, date/number formatting, translation framework

- **ORM with migration system** — database schema as code, automatic migrations|----------|---------------------|----------------------|#### Persona 4: Individual Owner (Vlastník)

- **django-simple-history** or **django-auditlog** — audit trail with minimal code

- **Mature ecosystem** — battle-tested, excellent documentation, large community| **Complexity** | ⭐ Single codebase, one language (Python) | ❌ Two separate apps (React frontend + API backend), two languages |- **Who:** An owner of one or more flats

- **Fast to develop** — a single developer can build the MVP quickly

| **Admin interface** | ⭐ Built-in Django Admin — ready-made CRUD for all models, free | ❌ Must build every admin screen from scratch |- **Goals:** View their own data, submit requests

**Why not React.js (as frontend)?**

- React is great for complex interactive SPAs, but Solomon is primarily **CRUD forms and tables**| **Audit trail** | ⭐ Mature Django packages (django-auditlog) handle this automatically | ❌ Must implement manually in the API layer |- **Access level:** Read-only access to their own relevant data (their flats, their financial records). Can submit change requests and repair requests but cannot edit data directly.

- React + Django = two separate apps (frontend + API), doubles the development effort

- For ~200 users viewing/editing property data, a full SPA is overengineered| **Localization** | ⭐ Django i18n is built-in, battle-tested, supports Czech | ⚠️ Must set up i18next or similar, more configuration |- **Typical tasks:** View their flat details, check utility costs, submit a repair request, request a data change (e.g., new phone number — but the change must be confirmed by admin/board)

- If interactivity is needed later, HTMX can be added incrementally

| **Authentication** | ⭐ Built-in user/group/permission system | ❌ Must implement or integrate (e.g., Auth0, NextAuth) |

#### Frontend: Django Templates + HTMX

- **Django Templates** — server-rendered HTML, fast to develop, SEO-friendly| **Development speed** | ⭐ One developer can build the full MVP quickly | ❌ Need frontend + backend expertise, more code to write |### 2.3 Modular Architecture (Conceptual)

- **HTMX** — adds dynamic behavior (inline editing, live search, partial page updates) without JavaScript framework overhead

- **CSS framework** — Tailwind CSS or Bootstrap for responsive design| **Hosting cost** | ⭐ Simple deployment, works on cheap shared hosting or VPS | ⚠️ Needs Node.js hosting for frontend + separate API server |The system is composed of independent modules. Each module can be designed, implemented, and deployed separately. All modules share a common foundation.

- This gives 90% of React's UX with 10% of the complexity

| **Maintenance** | ⭐ Single deployment, single stack to maintain | ❌ Two deployments, two dependency trees, more complexity |

#### Database: PostgreSQL

- Best open-source relational database| **User experience** | ⚠️ Server-rendered, but HTMX makes it feel snappy | ⭐ Rich SPA experience, but overkill for this app |```

- Excellent for structured data with relationships (buildings → flats → owners)

- Full-text search for Czech language┌─────────────────────────────────────────────────────────────────────┐

- JSON fields for flexible/future data

- Supported by all hosting providers**Verdict:** React.js is excellent for complex, highly interactive frontends (e.g., real-time dashboards, drag-and-drop interfaces). Solomon is primarily a **data management application** with CRUD forms, tables, and reports — Django's sweet spot. Adding HTMX gives Django apps a modern, responsive feel without the complexity of a full JavaScript framework.│                        FACILITY MANAGEMENT SYSTEM                   │



#### Why this stack works for Solomon:├─────────────────────────────────────────────────────────────────────┤



| Requirement | Django Solution |> **Note:** If in the future a rich interactive feature is needed (e.g., a drag-and-drop floor plan editor), a React component can be embedded into a Django page for just that feature.│                                                                     │

|-------------|----------------|

| CRUD for buildings, flats, owners, tenants | Django ORM + Admin + ModelForms |│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

| Role-based access (4 roles) | Django auth groups + permissions |

| Full audit trail | django-auditlog (automatic, per-field tracking) |#### 3.1.3 Why Not a Separate Frontend?│  │  🏗 Building  │  │  🏠 Flat     │  │  👤 Owner    │  MVP        │

| Czech localization | Django i18n (built-in Czech translation) |

| Soft deletes | django-safedelete library |│  │  Management  │  │  Management  │  │  Management  │  (Phase 1)  │

| Multi-language support | Django i18n framework |

| Web-based, responsive | Django Templates + Bootstrap/Tailwind |For Solomon specifically:│  └──────────────┘  └──────────────┘  └──────────────┘              │

| Small team / solo developer | Django's "batteries included" philosophy |

- **~200 users**, low traffic, simple CRUD — no need for SPA complexity│  ┌──────────────┐  ┌──────────────┐                                │

### 6.2 Hosting Analysis

- **One developer** (or small team) — maintaining one codebase is significantly easier│  │  🧑 Tenant   │  │  📋 Audit    │                  MVP          │

#### Option A: Google Cloud — Free Tier (Recommended to start)

- **Cloud Run** — free tier: 2M requests/month, 360K vCPU-seconds- **Audit trail and permissions** — Django handles this out of the box│  │  Management  │  │  Trail       │                  (Phase 1)    │

- **Cloud SQL (PostgreSQL)** — free trial ($300 credit for 90 days), then ~$7/month for smallest instance

- **Alternative:** Use **Cloud Run + SQLite** for MVP (zero DB cost), migrate to PostgreSQL later- **Speed to MVP** — Django Admin alone gives you a working admin interface in days│  └──────────────┘  └──────────────┘                                │

- **Pros:** Truly free to start, scales if needed, EU region available (europe-west1)

- **Cons:** Requires some DevOps knowledge, free tier may expire- **HTMX** bridges the gap — dynamic forms, inline editing, live search without a single line of React│                                                                     │



#### Option B: Railway.app / Render.com│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

- **Railway** — free trial, then ~$5/month. Very easy Django deployment.

- **Render** — free tier for web services (spins down after inactivity), PostgreSQL free for 90 days### 3.2 Hosting Analysis│  │  💰 Financial│  │  🔧 Utility  │  │  🛠 Mainten. │  Future     │

- **Pros:** Extremely easy deployment (git push = deploy), no DevOps needed

- **Cons:** Free tiers are limited, may spin down│  │  Management  │  │  Management  │  │  & Repairs   │  (Phase 2+) │



#### Option C: Czech VPS Hosting (~100–200 CZK/month)#### 3.2.1 Comparison of Hosting Options│  └──────────────┘  └──────────────┘  └──────────────┘              │

- **Wedos.cz** — VPS from 100 CZK/month, but primarily PHP hosting (Django would need VPS)

- **Hukot.net** — similar, good for PHP/WordPress, less convenient for Python/Django│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

- **Forpsi.com** — VPS options, Czech hosting

- **Pros:** Czech-based (GDPR), stable, predictable pricing| Option | Monthly Cost | Pros | Cons | Verdict |│  │  📢 Communi- │  │  🗳 Meetings │  │  📄 Document │  Future     │

- **Cons:** More manual setup, no free tier

|--------|-------------|------|------|---------|│  │  cation      │  │  & Voting    │  │  Management  │  (Phase 2+) │

#### Option D: Fly.io

- **Free tier:** 3 shared-cpu VMs, 256MB each, 3GB persistent storage| **Google Cloud Run (free tier)** | **~0 CZK** (free tier) | 2M requests/month free, auto-scales to zero, EU region (europe-west1), PostgreSQL free trial 90 days | PostgreSQL costs ~$7–10/month after trial. Requires Docker knowledge. Not truly free long-term for DB. | ⚠️ Good for experimentation, not truly free for production |│  └──────────────┘  └──────────────┘  └──────────────┘              │

- **Pros:** Generous free tier, easy Django deployment, EU regions

- **Cons:** Free tier may change, smaller community| **Google Cloud e2-micro** | **~0 CZK** (always free) | 1 free e2-micro VM, always free, 30 GB disk | Only US regions (not EU = GDPR concern). Very limited resources (0.25 vCPU, 1 GB RAM). Must manage everything yourself. | ❌ GDPR issue, too weak |│                                                                     │



#### Hosting Recommendation:| **Railway.com (Hobby)** | **~$5/month (~120 CZK)** | Deploy from GitHub, PostgreSQL included, automatic HTTPS, very easy setup | Limited to 0.5 GB RAM on free, custom domain costs extra on free plan | ⭐ Excellent for MVP/development |├─────────────────────────────────────────────────────────────────────┤



| Phase | Hosting | Cost | Why || **Hukot.net (VPS)** | **~100–200 CZK/month** | Czech hosting, Czech support, GDPR compliant, VPS with full control, PostgreSQL supported | Must manage server yourself (updates, security) | ⭐ Good for production, Czech-based |│  🔐 Authentication & Authorization │ 🌍 Localization (CZ primary) │

|-------|---------|------|-----|

| **Development** | Local (Docker) | Free | Fast iteration || **WEDOS/VEDOS (shared hosting)** | **~50–100 CZK/month** | Cheapest Czech option, Czech datacenters, GDPR ready | Shared hosting = PHP only, **no Python/Django support**. Would need WordPress or PHP framework. | ❌ Not suitable for Django |│  📝 Audit Trail Engine             │ 🔔 Notification Engine        │

| **MVP / Testing** | Fly.io or Railway | Free–$5/month | Easy deployment, free to start |

| **Production** | Czech VPS (Wedos/Forpsi) or Google Cloud Run | 100–200 CZK/month | GDPR, reliability, Czech location || **Fly.io** | **~0–$5/month** | Free tier with 3 shared VMs, PostgreSQL included, EU regions available | Free tier is very limited. Company is US-based. | ⚠️ Possible but limited |├─────────────────────────────────────────────────────────────────────┤



### 6.3 Project Structure (Preview)| **DigitalOcean App Platform** | **~$5/month (~120 CZK)** | EU regions (Amsterdam), easy deployment, managed database add-on | DB add-on costs extra ($7/month) | ⚠️ Good but adds up |│                    Shared Foundation / Common Services               │



```└─────────────────────────────────────────────────────────────────────┘

solomon/

├── manage.py#### 3.2.2 Recommended Hosting Strategy```

├── solomon/              # Django project settings

│   ├── settings.py

│   ├── urls.py

│   └── wsgi.py**Phase 1 (Development & MVP): Railway.com — Hobby plan ($5/month)**### 2.4 Key System Characteristics

├── core/                 # Shared: audit trail, auth, base models

│   ├── models.py         # AuditLog, SoftDeleteModel base- Deploy directly from GitHub repository- **Multi-building:** Supports 5 buildings under one SVJ, extensible

│   ├── middleware.py      # Current user tracking for audit

│   └── permissions.py    # Role-based permission classes- PostgreSQL database included- **Single management entity:** One administrator, one board (5 members + chairman)

├── buildings/            # Building management module

│   ├── models.py- Automatic HTTPS, custom domain support- **Multi-language:** Localization support with Czech as the primary language

│   ├── views.py

│   ├── forms.py- Zero server management — just push code- **Full audit trail:** Every data change is tracked with user, timestamp, diff, and effective date

│   └── templates/

├── flats/                # Flat management module- Perfect for getting the MVP running quickly- **Role-based access:** Four distinct roles with different permissions

├── owners/               # Owner management module

├── tenants/              # Tenant management module- **Modular:** Independent modules that can be built incrementally

├── templates/            # Shared templates (base, nav, etc.)

├── locale/               # Czech translations**Phase 2 (Production): Hukot.net — VPS (~150 CZK/month)**- **Czech legal context:** Designed for SVJ (primary) with housing cooperative as alternative

│   └── cs/

├── static/               # CSS, JS, images- Czech hosting, servers in Czech Republic → full GDPR compliance

├── Dockerfile

├── docker-compose.yml- Full control over the server (Ubuntu + Docker or direct install)---

└── requirements.txt

```- PostgreSQL, backups, enough resources for 200 users



---- Czech-language support, local company## 3. Architectural Design



## 7. Security Considerations- Long-term stable and affordable



### 7.1 Authentication### 3.1 Component Breakdown

- Django built-in auth (username/password, session-based)

- Password reset via email**Why not free hosting for production?**

- Optional 2FA for board members

- Google Cloud free tier is US-only (GDPR concern for Czech personal data)#### 3.1.1 Foundation Layer (shared by all modules)

### 7.2 Authorization — Role-Permission Matrix

- Free tiers are unreliable for production (resource limits, cold starts, no SLA)| Component | Responsibility |

| Action | Admin | Chairman | Board | Owner |

|--------|:---:|:---:|:---:|:---:|- Solomon handles personal data (GDPR) — you need a hosting provider that is GDPR compliant with EU-based servers|-----------|---------------|

| View all buildings/flats | ✅ | ✅ | ✅ | ❌ own only |

| Edit buildings/flats | ✅ | ✅ | ✅ | ❌ |- At ~150 CZK/month (~$6), a Czech VPS is extremely affordable and appropriate for an SVJ| **Auth & Identity** | User registration, login, session management, role assignment |

| View all owners/tenants | ✅ | ✅ | ✅ | ❌ own only |

| Edit owners/tenants | ✅ | ✅ | ✅ | ❌ request || **Authorization Engine** | Permission checks based on role (Admin, Chairman, Board Member, Owner) and data ownership |

| Submit repair request | ✅ | ✅ | ✅ | ✅ |

| Approve repair request | ✅ | ✅ | ✅ | ❌ |#### 3.2.3 Cost Summary| **Audit Trail Engine** | Intercepts all data modifications, records: user, timestamp, entity, field, old value, new value, effective date |

| Approve contracts above threshold | ❌ | ✅ | ❌ | ❌ |

| View full audit trail | ✅ | ✅ | ✅ | ❌ own only || **Localization Service** | Manages translations, date/currency/number formatting for Czech locale (and future languages) |

| Manage users/roles | ✅ | ✅ | ❌ | ❌ |

| Phase | Hosting | Database | Domain | Total || **Notification Engine** | Sends notifications (in-app, email) triggered by events (new request, approval needed, change recorded) |

### 7.3 Data Protection

- **GDPR compliance** — personal data of Czech/EU residents|-------|---------|----------|--------|-------|

- Encrypted at rest and in transit (HTTPS)

- Soft delete with anonymization after retention period| Development | Railway Hobby ($5) | Included | — | **~$5/month (120 CZK)** |#### 3.1.2 MVP Modules (Phase 1)

- Data processing consent required

| Production | Hukot VPS (~150 CZK) | Included (self-hosted PostgreSQL) | solomon.bdsalounova.cz (~0, subdomain) | **~150 CZK/month** |

---

**Module: Building Management (Správa budov)**

## 8. Performance and Scalability

- **Users:** ~5 admin/board + ~100–200 owners### 3.3 Component Breakdown| Aspect | Description |

- **Concurrent:** ~10–20 at peak

- **Data volume:** Thousands of records (small-scale)|--------|-------------|

- Standard Django caching and DB indexing is more than sufficient

#### 3.3.1 Foundation Layer (shared by all modules)| Responsibilities | Create, read, update, (soft-)delete buildings and their parameters |

---

| Component | Responsibility || Key data | Address, descriptive number, indicative number, floor plan, common rooms, number of floors, elevator (yes/no), year built, total units, land plot number, rental of common areas |

## 9. Deployment Architecture

|-----------|---------------|| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only, their buildings) |

### 9.1 Environments

- **Development** — local Docker (docker-compose)| **Auth & Identity** | User registration, login, session management, role assignment || Business rules | Deleting a building soft-deletes it (kept for history). All changes tracked via audit trail. |

- **Staging** — Fly.io or Railway free tier

- **Production** — Czech VPS or Google Cloud Run| **Authorization Engine** | Permission checks based on role (Admin, Chairman, Board Member, Owner) and data ownership |



### 9.2 CI/CD| **Audit Trail Engine** | Intercepts all data modifications, records: user, timestamp, entity, field, old value, new value, effective date |**Module: Flat Management (Správa bytových jednotek)**

- GitHub Actions for automated testing and deployment

- Repository: github.com/ondyn/Solomon| **Localization Service** | Manages translations, date/currency/number formatting for Czech locale (and future languages) || Aspect | Description |



---| **Notification Engine** | Sends notifications (in-app, email) triggered by events (new request, approval needed, change recorded) ||--------|-------------|



## 10. Testing Strategy| Responsibilities | Create, read, update, (soft-)delete flats and their parameters. Link flats to buildings. |

- **Unit tests** — Django TestCase for business logic (ownership shares, permissions, audit)

- **Integration tests** — module interactions (flat + owners + audit trail)#### 3.3.2 MVP Modules (Phase 1)| Key data | Area, number of rooms, layout, floor number, water outlets count, waste outlets count, number of radiators, radiator power, gas installed (yes/no), balcony (yes/no), cellar unit, unit ownership certificate number |

- **E2E tests** — critical flows (login → view flat → submit request)

- **Localization tests** — Czech strings completeness| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only, their flats) |



---**Module: Building Management (Správa budov)**| Business rules | Each flat belongs to exactly one building. A flat can have multiple owners and multiple tenants. All changes tracked. |



## 11. Appendices| Aspect | Description |



### 11.1 Glossary|--------|-------------|**Module: Owner Management (Správa vlastníků)**

See section 1.5.

| Responsibilities | Create, read, update, (soft-)delete buildings and their parameters || Aspect | Description |

### 11.2 Related Resources

- External website: https://www.bdsalounova.cz/| Key data | Address, descriptive number, indicative number, floor plan, common rooms, number of floors, elevator (yes/no), year built, total units, land plot number, rental of common areas ||--------|-------------|

- Repository: https://github.com/ondyn/Solomon

- Czech Civil Code — SVJ: §1158–§1222| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only, their buildings) || Responsibilities | Create, read, update, (soft-)delete owners. Link owners to flats. Manage co-ownership. |

- Czech Act on Business Corporations — Housing Cooperatives: §727–§757

| Business rules | Deleting a building soft-deletes it (kept for history). All changes tracked via audit trail. || Key data | Name (natural or legal person), permanent address, contact address, phone, email, deputy/representative, ownership share size, move-in date, notes |

### 11.3 Change History

| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only for their own record, can submit change requests) |

| Version | Date | Author | Changes |

|---------|------|--------|---------|**Module: Flat Management (Správa bytových jednotek)**| Business rules | One owner can own multiple flats (1:N). One flat can have multiple owners — co-ownership (M:N) with share sizes. Ownership share is expressed as a fraction/percentage. Ownership changes must have an effective date. |

| 0.1 | 2026-03-03 | — | Initial draft: Introduction, definitions |

| 0.2 | 2026-03-03 | — | System description, architecture, ER diagram, role-permission matrix || Aspect | Description |

| 0.3 | 2026-03-03 | — | Technology stack: Django + HTMX + PostgreSQL. Hosting analysis. Project structure. |

|--------|-------------|**Module: Tenant Management (Správa nájemníků)**

| Responsibilities | Create, read, update, (soft-)delete flats and their parameters. Link flats to buildings. || Aspect | Description |

| Key data | Area, number of rooms, layout, floor number, water outlets count, waste outlets count, number of radiators, radiator power, gas installed (yes/no), balcony (yes/no), cellar unit, unit ownership certificate number ||--------|-------------|

| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only, their flats) || Responsibilities | Create, read, update, (soft-)delete tenants. Link tenants to flats (and indirectly to owners). |

| Business rules | Each flat belongs to exactly one building. A flat can have multiple owners and multiple tenants. All changes tracked. || Key data | Name, permanent address, contact address, phone, email, lease start date, lease end date, notes |

| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only for tenants in their flats) |

**Module: Owner Management (Správa vlastníků)**| Business rules | One flat can have multiple tenants. Tenants are linked to the flat, not directly to the owner. Tenant records are soft-deleted when they move out (kept for history). |

| Aspect | Description |

|--------|-------------|**Module: Audit Trail (Historie změn)**

| Responsibilities | Create, read, update, (soft-)delete owners. Link owners to flats. Manage co-ownership. || Aspect | Description |

| Key data | Name (natural or legal person), permanent address, contact address, phone, email, deputy/representative, ownership share size, move-in date, notes ||--------|-------------|

| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only for their own record, can submit change requests) || Responsibilities | Automatically record every data change across all modules |

| Business rules | One owner can own multiple flats (1:N). One flat can have multiple owners — co-ownership (M:N) with share sizes. Ownership share is expressed as a fraction/percentage. Ownership changes must have an effective date. || Key data per record | Timestamp, user who made the change, entity type, entity ID, field name, old value, new value, effective date |

| Users | Administrator, Chairman (full access); Board Members (read access); Individual Owners (audit trail for their own data only) |

**Module: Tenant Management (Správa nájemníků)**| Business rules | Audit records are immutable — they can never be edited or deleted. The effective date may differ from the system timestamp (e.g., ownership transferred on Jan 1 but recorded on Jan 15). |

| Aspect | Description |

|--------|-------------|#### 3.1.3 Future Modules (Phase 2+) — Conceptual Overview

| Responsibilities | Create, read, update, (soft-)delete tenants. Link tenants to flats (and indirectly to owners). |

| Key data | Name, permanent address, contact address, phone, email, lease start date, lease end date, notes |**Module: Financial Management (Finanční správa)**

| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only for tenants in their flats) |- Track income (monthly fees/advances from owners) and expenses (repairs, services, hardware)

| Business rules | One flat can have multiple tenants. Tenants are linked to the flat, not directly to the owner. Tenant records are soft-deleted when they move out (kept for history). |- Simplified cost tracking per project, repair, or service — not full double-entry bookkeeping

- Annual settlement of utilities per flat based on flat parameters

**Module: Audit Trail (Historie změn)**- Repair fund / long-term maintenance fund tracking

| Aspect | Description |- Approval workflow: expenses above a threshold require Chairman approval

|--------|-------------|

| Responsibilities | Automatically record every data change across all modules |**Module: Utility Management (Správa energií a médií)**

| Key data per record | Timestamp, user who made the change, entity type, entity ID, field name, old value, new value, effective date |- Record meter readings (water, gas, heat) per flat

| Users | Administrator, Chairman (full access); Board Members (read access); Individual Owners (audit trail for their own data only) |- Calculate utility costs per flat based on parameters (area, outlets, radiators, etc.)

| Business rules | Audit records are immutable — they can never be edited or deleted. The effective date may differ from the system timestamp (e.g., ownership transferred on Jan 1 but recorded on Jan 15). |- Support for both manual entry and future integration with utility providers

- Annual settlement and comparison reports

#### 3.3.3 Future Modules (Phase 2+) — Conceptual Overview

**Module: Maintenance & Repairs (Údržba a opravy)**

**Module: Financial Management (Finanční správa)**- Submit repair/maintenance requests (any user)

- Track income (monthly fees/advances from owners) and expenses (repairs, services, hardware)- Request lifecycle: Submitted → Approved → In Progress → Completed / Rejected

- Simplified cost tracking per project, repair, or service — not full double-entry bookkeeping- Board member approval required; Chairman approval for contracts above defined threshold

- Annual settlement of utilities per flat based on flat parameters- Schedule recurring maintenance (elevator inspection, chimney cleaning, etc.)

- Repair fund / long-term maintenance fund tracking- Manage contracts with external service providers

- Approval workflow: expenses above a threshold require Chairman approval

**Module: Communication (Komunikace)**

**Module: Utility Management (Správa energií a médií)**- Internal announcements to all residents or specific buildings

- Record meter readings (water, gas, heat) per flat- Notification engine (in-app + email)

- Calculate utility costs per flat based on parameters (area, outlets, radiators, etc.)- Integration note: External public website exists at https://www.bdsalounova.cz/ (WordPress) — the FM system handles internal communication only

- Support for both manual entry and future integration with utility providers

- Annual settlement and comparison reports**Module: Meetings & Voting (Schůze a hlasování)**

- Plan SVJ member meetings

**Module: Maintenance & Repairs (Údržba a opravy)**- Record meeting minutes and resolutions

- Submit repair/maintenance requests (any user)- Track votes (per owner, weighted by ownership share)

- Request lifecycle: Submitted → Approved → In Progress → Completed / Rejected- Quorum management

- Board member approval required; Chairman approval for contracts above defined threshold- Archive of past meetings and decisions

- Schedule recurring maintenance (elevator inspection, chimney cleaning, etc.)

- Manage contracts with external service providers**Module: Document Management (Správa dokumentů)**

- Store and organize documents: contracts, certificates, house rules, insurance policies, floor plans, meeting minutes

**Module: Communication (Komunikace)**- Version control for documents

- Internal announcements to all residents or specific buildings- Access control: some documents visible to all owners, some restricted to board

- Notification engine (in-app + email)

- Integration note: External public website exists at https://www.bdsalounova.cz/ (WordPress) — the FM system handles internal communication only### 3.2 Data Flow — User Perspective



**Module: Meetings & Voting (Schůze a hlasování)**```

- Plan SVJ member meetings┌─────────┐     request      ┌──────────────┐     permission     ┌──────────────┐

- Record meeting minutes and resolutions│  Owner   │ ──────────────► │  Application  │ ◄───────────────► │  Auth &      │

- Track votes (per owner, weighted by ownership share)│  (view / │                 │  Layer        │    check           │  Authorization│

- Quorum management│  request)│ ◄────────────── │               │                   └──────────────┘

- Archive of past meetings and decisions└─────────┘   filtered data  │               │

                              │               │     log every     ┌──────────────┐

**Module: Document Management (Správa dokumentů)**┌─────────┐     full CRUD    │               │ ──────────────►   │  Audit Trail │

- Store and organize documents: contracts, certificates, house rules, insurance policies, floor plans, meeting minutes│  Admin / │ ──────────────► │               │     change         │  Engine      │

- Version control for documents│  Board   │                 │               │                   └──────────────┘

- Access control: some documents visible to all owners, some restricted to board│          │ ◄────────────── │               │

└─────────┘    full data     │               │     notify         ┌──────────────┐

### 3.4 Data Flow — User Perspective                              │               │ ──────────────►   │  Notification│

┌─────────┐   approve /      │               │     relevant      │  Engine      │

```│ Chairman │   reject         │               │     users         └──────────────┘

┌─────────┐     request      ┌──────────────┐     permission     ┌──────────────┐│          │ ──────────────► │               │

│  Owner   │ ──────────────► │  Django       │ ◄───────────────► │  Auth &      │└─────────┘                  └──────────────┘

│  (view / │                 │  Application  │    check           │  Authorization│                                    │

│  request)│ ◄────────────── │               │                   └──────────────┘                                    ▼

└─────────┘   filtered data  │               │                             ┌──────────────┐

                              │               │     log every     ┌──────────────┐                             │   Database    │

┌─────────┐     full CRUD    │               │ ──────────────►   │  Audit Trail │                             └──────────────┘

│  Admin / │ ──────────────► │               │     change         │  (django-    │```

│  Board   │                 │               │                   │  auditlog)   │

│          │ ◄────────────── │               │                   └──────────────┘### 3.3 Technology Stack

└─────────┘    full data     │               │> To be decided in technical design phase. No technology choices are made at this stage.

                              │               │     notify         ┌──────────────┐

┌─────────┐   approve /      │               │ ──────────────►   │  Email /     │---

│ Chairman │   reject         │               │     relevant      │  In-app      │

│          │ ──────────────► │               │     users         │  Notifications│## 4. Detailed Design

└─────────┘                  └──────────────┘                    └──────────────┘

                                    │> **Note:** Detailed design will be elaborated per module during implementation. Below is the structure for MVP modules.

                                    ▼

                             ┌──────────────┐### 4.1 Module: Building Management

                             │  PostgreSQL   │

                             └──────────────┘| Aspect | Detail |

```|--------|--------|

| **Responsibilities** | CRUD for buildings. Store building parameters. Link flats to buildings. |

---| **Inputs** | Building data (address, parameters), user identity |

| **Outputs** | Building records, building list (filtered by user role), change history |

## 4. Detailed Design| **Error Handling** | Validation errors for required fields (address, descriptive number). Prevent deletion of buildings that contain active flats. |

| **Business Rules** | Soft delete only. All changes produce audit trail entries. |

> **Note:** Detailed design will be elaborated per module during implementation. Below is the structure for MVP modules.

### 4.2 Module: Flat Management

### 4.1 Module: Building Management

| Aspect | Detail |

| Aspect | Detail ||--------|--------|

|--------|--------|| **Responsibilities** | CRUD for flats. Store flat parameters. Link to building, owners, tenants. |

| **Responsibilities** | CRUD for buildings. Store building parameters. Link flats to buildings. || **Inputs** | Flat data (area, rooms, layout, etc.), building reference, user identity |

| **Inputs** | Building data (address, parameters), user identity || **Outputs** | Flat records, flat list per building, owners/tenants per flat, change history |

| **Outputs** | Building records, building list (filtered by user role), change history || **Error Handling** | Validation for required fields. Area must be positive number. Floor number must be within building's floor count. |

| **Error Handling** | Validation errors for required fields (address, descriptive number). Prevent deletion of buildings that contain active flats. || **Business Rules** | Each flat belongs to exactly one building. Co-ownership supported via M:N link with share size. Soft delete only. |

| **Business Rules** | Soft delete only. All changes produce audit trail entries. |

### 4.3 Module: Owner Management

### 4.2 Module: Flat Management

| Aspect | Detail |

| Aspect | Detail ||--------|--------|

|--------|--------|| **Responsibilities** | CRUD for owners (natural or legal persons). Link to flats with ownership share. |

| **Responsibilities** | CRUD for flats. Store flat parameters. Link to building, owners, tenants. || **Inputs** | Owner data (name, type, contacts, deputy, share size), flat references, effective dates |

| **Inputs** | Flat data (area, rooms, layout, etc.), building reference, user identity || **Outputs** | Owner records, owned flats list, ownership history, contact details |

| **Outputs** | Flat records, flat list per building, owners/tenants per flat, change history || **Error Handling** | Validate share sizes sum to 100% per flat (warning if not). Validate required contact fields. |

| **Error Handling** | Validation for required fields. Area must be positive number. Floor number must be within building's floor count. || **Business Rules** | Ownership changes must have an effective date. An owner can be a natural person or a legal person (company). Deputy/representative can be specified. Soft delete preserves history. |

| **Business Rules** | Each flat belongs to exactly one building. Co-ownership supported via M:N link with share size. Soft delete only. |

### 4.4 Module: Tenant Management

### 4.3 Module: Owner Management

| Aspect | Detail |

| Aspect | Detail ||--------|--------|

|--------|--------|| **Responsibilities** | CRUD for tenants. Link to flats. Track lease periods. |

| **Responsibilities** | CRUD for owners (natural or legal persons). Link to flats with ownership share. || **Inputs** | Tenant data (name, contacts), flat reference, lease dates |

| **Inputs** | Owner data (name, type, contacts, deputy, share size), flat references, effective dates || **Outputs** | Tenant records, tenants per flat, lease history |

| **Outputs** | Owner records, owned flats list, ownership history, contact details || **Error Handling** | Validate lease dates (start < end). Warn if overlapping tenancies exceed expected capacity. |

| **Error Handling** | Validate share sizes sum to 100% per flat (warning if not). Validate required contact fields. || **Business Rules** | Multiple tenants per flat allowed. Tenants linked to flat, not directly to owner. Moving out = soft delete with end date. |

| **Business Rules** | Ownership changes must have an effective date. An owner can be a natural person or a legal person (company). Deputy/representative can be specified. Soft delete preserves history. |

### 4.5 Module: Audit Trail

### 4.4 Module: Tenant Management

| Aspect | Detail |

| Aspect | Detail ||--------|--------|

|--------|--------|| **Responsibilities** | Automatically capture and store all data changes across all modules |

| **Responsibilities** | CRUD for tenants. Link to flats. Track lease periods. || **Inputs** | Triggered automatically on every create/update/delete operation |

| **Inputs** | Tenant data (name, contacts), flat reference, lease dates || **Outputs** | Chronological log viewable per entity, per user, or globally. Filterable by date range, entity type, user, field. |

| **Outputs** | Tenant records, tenants per flat, lease history || **Error Handling** | Audit trail writes must never fail silently — if audit cannot be recorded, the original operation should also fail (transactional). |

| **Error Handling** | Validate lease dates (start < end). Warn if overlapping tenancies exceed expected capacity. || **Business Rules** | Immutable records. Two dates per entry: system timestamp (when recorded) and effective date (since when it applies). Searchable and exportable. |

| **Business Rules** | Multiple tenants per flat allowed. Tenants linked to flat, not directly to owner. Moving out = soft delete with end date. |

---

### 4.5 Module: Audit Trail

## 5. Database Design

| Aspect | Detail |

|--------|--------|### 5.1 Conceptual ER Diagram

| **Responsibilities** | Automatically capture and store all data changes across all modules |

| **Inputs** | Triggered automatically on every create/update/delete operation |```mermaid

| **Outputs** | Chronological log viewable per entity, per user, or globally. Filterable by date range, entity type, user, field. |erDiagram

| **Error Handling** | Audit trail writes must never fail silently — if audit cannot be recorded, the original operation should also fail (transactional). |    BUILDING ||--o{ FLAT : contains

| **Business Rules** | Immutable records. Two dates per entry: system timestamp (when recorded) and effective date (since when it applies). Searchable and exportable. |    FLAT ||--o{ FLAT_OWNER : "owned by"

    OWNER ||--o{ FLAT_OWNER : "owns"

---    FLAT ||--o{ TENANT : "rented by"



## 5. Database Design    USER ||--o{ AUDIT_LOG : "performs"



### 5.1 Conceptual ER Diagram    BUILDING {

        id UUID PK

```mermaid        address string

erDiagram        descriptive_number string

    BUILDING ||--o{ FLAT : contains        indicative_number string

    FLAT ||--o{ FLAT_OWNER : "owned by"        number_of_floors int

    OWNER ||--o{ FLAT_OWNER : "owns"        elevator boolean

    FLAT ||--o{ TENANT : "rented by"        year_built int

        total_units int

    USER ||--o{ AUDIT_LOG : "performs"        land_plot_number string

        common_rooms text

    BUILDING {        floor_plan_url string

        id UUID PK        common_area_rental text

        address string        notes text

        descriptive_number string        is_deleted boolean

        indicative_number string        created_at datetime

        number_of_floors int        updated_at datetime

        elevator boolean    }

        year_built int

        total_units int    FLAT {

        land_plot_number string        id UUID PK

        common_rooms text        building_id UUID FK

        floor_plan_url string        unit_number string

        common_area_rental text        area_sqm decimal

        notes text        number_of_rooms int

        is_deleted boolean        layout string

        created_at datetime        floor_number int

        updated_at datetime        water_outlets int

    }        waste_outlets int

        radiator_count int

    FLAT {        radiator_power_kw decimal

        id UUID PK        gas_installed boolean

        building_id UUID FK        has_balcony boolean

        unit_number string        cellar_unit string

        area_sqm decimal        ownership_certificate_number string

        number_of_rooms int        notes text

        layout string        is_deleted boolean

        floor_number int        created_at datetime

        water_outlets int        updated_at datetime

        waste_outlets int    }

        radiator_count int

        radiator_power_kw decimal    OWNER {

        gas_installed boolean        id UUID PK

        has_balcony boolean        person_type enum "natural or legal"

        cellar_unit string        name string

        ownership_certificate_number string        permanent_address string

        notes text        contact_address string

        is_deleted boolean        phone string

        created_at datetime        email string

        updated_at datetime        deputy_name string

    }        deputy_contact string

        move_in_date date

    OWNER {        notes text

        id UUID PK        is_deleted boolean

        person_type enum "natural or legal"        created_at datetime

        name string        updated_at datetime

        permanent_address string    }

        contact_address string

        phone string    FLAT_OWNER {

        email string        id UUID PK

        deputy_name string        flat_id UUID FK

        deputy_contact string        owner_id UUID FK

        move_in_date date        share_numerator int

        notes text        share_denominator int

        is_deleted boolean        effective_from date

        created_at datetime        effective_to date

        updated_at datetime        notes text

    }    }



    FLAT_OWNER {    TENANT {

        id UUID PK        id UUID PK

        flat_id UUID FK        flat_id UUID FK

        owner_id UUID FK        name string

        share_numerator int        permanent_address string

        share_denominator int        contact_address string

        effective_from date        phone string

        effective_to date        email string

        notes text        lease_start date

    }        lease_end date

        notes text

    TENANT {        is_deleted boolean

        id UUID PK        created_at datetime

        flat_id UUID FK        updated_at datetime

        name string    }

        permanent_address string

        contact_address string    USER {

        phone string        id UUID PK

        email string        owner_id UUID FK "nullable"

        lease_start date        username string

        lease_end date        role enum "admin/chairman/board_member/owner"

        notes text        language_preference string

        is_deleted boolean        is_active boolean

        created_at datetime        created_at datetime

        updated_at datetime    }

    }

    AUDIT_LOG {

    USER {        id UUID PK

        id UUID PK        user_id UUID FK

        owner_id UUID FK "nullable"        entity_type string

        username string        entity_id UUID

        role enum "admin/chairman/board_member/owner"        action enum "create/update/delete"

        language_preference string        field_name string

        is_active boolean        old_value text

        created_at datetime        new_value text

    }        effective_date date

        recorded_at datetime

    AUDIT_LOG {    }

        id UUID PK```

        user_id UUID FK

        entity_type string### 5.2 Key Relationships

        entity_id UUID| Relationship | Type | Description |

        action enum "create/update/delete"|-------------|------|-------------|

        field_name string| Building → Flat | 1:N | A building contains many flats |

        old_value text| Flat ↔ Owner | M:N | Via `FLAT_OWNER` junction table. Includes share size and effective dates. |

        new_value text| Flat → Tenant | 1:N | A flat can have multiple tenants |

        effective_date date| User → Owner | 1:1 (optional) | An owner may have a user account. Admin/board users may not be owners. |

        recorded_at datetime| User → Audit Log | 1:N | Every user action is logged |

    }

```### 5.3 Design Principles

- **Soft deletes** everywhere — `is_deleted` flag, never hard delete

### 5.2 Key Relationships- **Temporal data** — ownership and tenancy use `effective_from` / `effective_to` dates

| Relationship | Type | Description |- **Immutable audit log** — append-only, no updates or deletes

|-------------|------|-------------|- **UUID primary keys** — for future flexibility and security (no sequential IDs exposed)

| Building → Flat | 1:N | A building contains many flats |

| Flat ↔ Owner | M:N | Via `FLAT_OWNER` junction table. Includes share size and effective dates. |---

| Flat → Tenant | 1:N | A flat can have multiple tenants |

| User → Owner | 1:1 (optional) | An owner may have a user account. Admin/board users may not be owners. |## 6. External Interfaces

| User → Audit Log | 1:N | Every user action is logged |

### 6.1 User Interface

### 5.3 Design Principles- **Web application** — responsive design, accessible from desktop and mobile browsers

- **Soft deletes** everywhere — `is_deleted` flag, never hard delete- **Primary language:** Czech (česky)

- **Temporal data** — ownership and tenancy use `effective_from` / `effective_to` dates- **Localization:** Multi-language support built in, additional languages can be added

- **Immutable audit log** — append-only, no updates or deletes- **Key UI patterns:**

- **UUID primary keys** — for future flexibility and security (no sequential IDs exposed)    - Dashboard per role (Admin sees everything, Owner sees their data)

    - CRUD forms with validation

---    - History/changelog viewer per entity

    - Search and filter across all entities

## 6. External Interfaces    - Approval workflows (visual status indicators)



### 6.1 User Interface### 6.2 External Integrations

- **Web application** — responsive design, accessible from desktop and mobile browsers- **WordPress website** (https://www.bdsalounova.cz/) — exists independently, no direct integration in MVP. Future consideration: push announcements from FM system to website.

- **Primary language:** Czech (česky)- **Email** — for notifications (change confirmations, request status updates, board approvals)

- **Localization:** Multi-language support built in, additional languages can be added- **No hardware interfaces** in MVP

- **Technology:** Django Templates + HTMX for dynamic interactions

- **Key UI patterns:**### 6.3 Communication Protocols

    - Dashboard per role (Admin sees everything, Owner sees their data)- To be defined during technical design phase (REST API, GraphQL, etc.)

    - CRUD forms with validation

    - History/changelog viewer per entity---

    - Search and filter across all entities

    - Approval workflows (visual status indicators)## 7. Security Considerations



### 6.2 External Integrations### 7.1 Authentication

- **WordPress website** (https://www.bdsalounova.cz/) — exists independently, no direct integration in MVP. Future consideration: push announcements from FM system to website.- Secure login with username/password

- **Email** — for notifications (change confirmations, request status updates, board approvals)- Consider: password reset via email, optional two-factor authentication for board members

- **No hardware interfaces** in MVP

### 7.2 Authorization — Role-Permission Matrix

### 6.3 Communication Protocols

- Standard HTTP/HTTPS (Django serves both HTML and any future API endpoints)| Action | Administrator | Chairman | Board Member | Owner |

- REST API can be added later via Django REST Framework if needed (e.g., for mobile app or external integrations)|--------|:---:|:---:|:---:|:---:|

| View all buildings/flats | ✅ | ✅ | ✅ | ❌ (own only) |

---| Edit buildings/flats | ✅ | ✅ | ✅ | ❌ |

| View all owners/tenants | ✅ | ✅ | ✅ | ❌ (own only) |

## 7. Security Considerations| Edit owners/tenants | ✅ | ✅ | ✅ | ❌ (submit request) |

| Submit repair request | ✅ | ✅ | ✅ | ✅ |

### 7.1 Authentication| Approve repair request | ✅ | ✅ | ✅ | ❌ |

- Django built-in authentication system| Approve contracts above threshold | ❌ | ✅ | ❌ | ❌ |

- Secure login with username/password| View full audit trail | ✅ | ✅ | ✅ (read) | ❌ (own only) |

- Password reset via email| Manage users and roles | ✅ | ✅ | ❌ | ❌ |

- Optional: two-factor authentication for board members (django-two-factor-auth)

### 7.3 Data Protection

### 7.2 Authorization — Role-Permission Matrix- **GDPR compliance** — the system processes personal data of Czech/EU residents

    - Right to access: owners can view their data

| Action | Administrator | Chairman | Board Member | Owner |    - Right to rectification: owners can request corrections

|--------|:---:|:---:|:---:|:---:|    - Right to erasure: soft delete with data anonymization after retention period

| View all buildings/flats | ✅ | ✅ | ✅ | ❌ (own only) |    - Data processing consent must be obtained

| Edit buildings/flats | ✅ | ✅ | ✅ | ❌ |    - Personal data must be stored securely (encrypted at rest and in transit)

| View all owners/tenants | ✅ | ✅ | ✅ | ❌ (own only) |- **Data retention policy** to be defined (legal minimum for SVJ records)

| Edit owners/tenants | ✅ | ✅ | ✅ | ❌ (submit request) |

| Submit repair request | ✅ | ✅ | ✅ | ✅ |### 7.4 Threat Model

| Approve repair request | ✅ | ✅ | ✅ | ❌ |- Low user count (~50–200 users), but data is sensitive (personal data, financial)

| Approve contracts above threshold | ❌ | ✅ | ❌ | ❌ |- Key threats: unauthorized access to other owners' data, privilege escalation, data tampering

| View full audit trail | ✅ | ✅ | ✅ (read) | ❌ (own only) |- Mitigations: role-based access control, audit trail, input validation, HTTPS

| Manage users and roles | ✅ | ✅ | ❌ | ❌ |

---

### 7.3 Data Protection

- **GDPR compliance** — the system processes personal data of Czech/EU residents## 8. Performance and Scalability

    - Right to access: owners can view their data

    - Right to rectification: owners can request corrections### 8.1 Expected Load

    - Right to erasure: soft delete with data anonymization after retention period- **Users:** ~5 administrators/board + ~100–200 individual owners

    - Data processing consent must be obtained- **Concurrent users:** ~10–20 at peak

    - Personal data must be stored securely (encrypted at rest and in transit)- **Data volume:** Small — thousands of records, not millions

- **Data retention policy** to be defined (legal minimum for SVJ records)- **Traffic pattern:** Low and steady, with occasional spikes during annual meetings or utility settlements

- **Hosting in Czech Republic / EU** for GDPR compliance

### 8.2 Scalability Considerations

### 7.4 Threat Model- The system is small-scale by nature — performance optimization is not a primary concern

- Low user count (~50–200 users), but data is sensitive (personal data, financial)- Standard caching and database indexing will be sufficient

- Key threats: unauthorized access to other owners' data, privilege escalation, data tampering- Architecture should be clean and maintainable rather than optimized for massive scale

- Mitigations: role-based access control, audit trail, input validation, HTTPS, Django's built-in CSRF/XSS protection

---

---

## 9. Deployment Architecture

## 8. Performance and Scalability

> To be defined during technical design phase. Key considerations:

### 8.1 Expected Load

- **Users:** ~5 administrators/board + ~100–200 individual owners### 9.1 Environments

- **Concurrent users:** ~10–20 at peak- **Development** — local developer environment

- **Data volume:** Small — thousands of records, not millions- **Staging** — for testing before production releases

- **Traffic pattern:** Low and steady, with occasional spikes during annual meetings or utility settlements- **Production** — the live system



### 8.2 Scalability Considerations### 9.2 Hosting Considerations

- The system is small-scale by nature — performance optimization is not a primary concern- Small-scale application, can be hosted on a single server or small cloud instance

- Django + PostgreSQL on a basic VPS is more than sufficient- Czech/EU hosting preferred for GDPR compliance

- Standard database indexing will be sufficient- External website (WordPress) is hosted separately

- Architecture should be clean and maintainable rather than optimized for massive scale

---

---

## 10. Testing Strategy

## 9. Deployment Architecture

> To be defined during technical design phase. Key principles:

### 9.1 Environments

- **Development** — local developer machine (Django development server + SQLite or local PostgreSQL)- **Unit tests** for business logic (ownership share validation, permission checks, audit trail)

- **Staging** — Railway.com (development/testing phase)- **Integration tests** for module interactions (creating a flat with owners, audit trail recording)

- **Production** — Czech VPS (Hukot.net or similar, Ubuntu + Docker)- **End-to-end tests** for critical user flows (login → view flat → submit request → approval)

- **Localization tests** — verify Czech language strings are complete and correct

### 9.2 Deployment Stack

```---

┌─────────────────────────────────────┐

│         Czech VPS (Hukot.net)       │## 11. Appendices

│                                     │

│  ┌───────────────────────────────┐  │### 11.1 Glossary

│  │         Nginx (reverse proxy) │  │See section 1.5 for full glossary of terms.

│  │         HTTPS (Let's Encrypt) │  │

│  └──────────────┬────────────────┘  │### 11.2 Related Resources

│                 │                    │- External website: https://www.bdsalounova.cz/

│  ┌──────────────▼────────────────┐  │- Czech Civil Code (Občanský zákoník) — SVJ regulation: §1158–§1222

│  │    Gunicorn (WSGI server)     │  │- Czech Act on Business Corporations — Housing Cooperatives: §727–§757

│  │    Django Application         │  │

│  └──────────────┬────────────────┘  │### 11.3 Change History

│                 │                    │

│  ┌──────────────▼────────────────┐  │| Version | Date | Author | Changes |

│  │        PostgreSQL             │  │|---------|------|--------|---------|

│  └───────────────────────────────┘  │| 0.1 | 2026-03-03 | — | Initial draft: Introduction, definitions |

│                                     │| 0.2 | 2026-03-03 | — | Full system description, modular architecture, MVP scope, ER diagram, role-permission matrix |

│  Automated backups (daily)          │
└─────────────────────────────────────┘
```

### 9.3 CI/CD Pipeline
- **Source code:** GitHub (repository: ondyn/Solomon)
- **CI:** GitHub Actions — run tests, linting on every push
- **CD:** Auto-deploy to staging (Railway) on push to `develop` branch; manual deploy to production on `main` branch
- **Backups:** Automated daily PostgreSQL dumps to external storage

### 9.4 Cost Summary

| Item | Development Phase | Production Phase |
|------|------------------|-----------------|
| Hosting | Railway Hobby ~$5/month | Czech VPS ~150 CZK/month |
| Database | Included | Self-hosted PostgreSQL (included) |
| Domain | — | solomon.bdsalounova.cz (subdomain, free) |
| SSL | Included (Railway) | Let's Encrypt (free) |
| Email | — | SMTP service (free tier or ~50 CZK/month) |
| **Total** | **~120 CZK/month** | **~150–200 CZK/month** |

---

## 10. Testing Strategy

### 10.1 Testing Approach
- **Unit tests** — Django TestCase for business logic (ownership share validation, permission checks, audit trail)
- **Integration tests** — test module interactions (creating a flat with owners, audit trail recording)
- **End-to-end tests** — Selenium or Playwright for critical user flows (login → view flat → submit request → approval)
- **Localization tests** — verify Czech language strings are complete and correct

### 10.2 Quality Metrics
- Code coverage target: 80%+ for business logic
- All audit trail functionality must be 100% tested
- Permission checks must be 100% tested (security-critical)

---

## 11. Appendices

### 11.1 Glossary
See section 1.5 for full glossary of terms.

### 11.2 Related Resources
- External website: https://www.bdsalounova.cz/
- GitHub repository: https://github.com/ondyn/Solomon
- Czech Civil Code (Občanský zákoník) — SVJ regulation: §1158–§1222
- Czech Act on Business Corporations — Housing Cooperatives: §727–§757

### 11.3 Technology References
- Django: https://www.djangoproject.com/
- HTMX: https://htmx.org/
- django-auditlog: https://github.com/jazzband/django-auditlog
- PostgreSQL: https://www.postgresql.org/
- Railway: https://railway.com/
- Hukot.net: https://www.hukot.net/

### 11.4 Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-03-03 | — | Initial draft: Introduction, definitions |
| 0.2 | 2026-03-03 | — | Full system description, modular architecture, MVP scope, ER diagram, role-permission matrix |
| 0.3 | 2026-03-03 | — | Application named "Solomon". Technology stack decision (Django + PostgreSQL + HTMX). Hosting analysis and recommendation. Deployment architecture. |
