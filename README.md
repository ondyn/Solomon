# Solomon — Facility Management System (BD Salounova)# Facility Management System — BD Salounova# Facility Management System



## Software Design Document



---## Software Design Document## Software Design Document



## 1. Introduction1. ### Introduction



### 1.1 Purpose---- Purpose: Facility management system

A facility management system designed for managing residential property — specifically a row of interconnected apartment buildings (house of flats) operated under a single legal entity (SVJ or Housing Cooperative) in the Czech Republic. The system replaces existing manual processes and spreadsheets used by the property manager.

- Scope: Users will be able to handle all tasks related to manage their property. Usually house of flats and all related tasks.

### 1.2 Scope

Users will be able to handle all tasks related to managing their property: building and flat registry, owner and tenant management, financial tracking, utility management, maintenance and repairs, communication, meetings, and document management. The system is designed as a set of **independent modules** that can be designed and implemented incrementally.## 1. Introduction- Definitions and Acronyms: 



### 1.3 MVP Scope (Phase 1)    - Flat: The building contains several apartments (flats) with different parameters (area, number of rooms, number of water and waste outlets, number of radiators and their power, whether gas is installed, etc.) 

The first version of the system focuses on the **core property registry**:

- **Building management** — CRUD operations for buildings and their parameters### 1.1 Purpose    - Building: Building contains flats and has its own parameters as floor plan, common rooms (such as laundry room, drying room, bike room, workshop), address, descriptive and indicative number, 

- **Flat management** — CRUD operations for flats/units and their parameters

- **Owner management** — CRUD operations for owners (natural or legal persons), including co-ownershipA facility management system designed for managing residential property — specifically a row of interconnected apartment buildings (house of flats) operated under a single legal entity (SVJ or Housing Cooperative) in the Czech Republic. The system replaces existing manual processes and spreadsheets used by the property manager.    - Owner: Unit which owns the flat (Association of Unit Owners) or have the right to use the flat (housing cooperative)

- **Tenant management** — CRUD operations for tenants, linked to flats and owners

- **Full audit trail** — Every change is recorded: who made it, when, what changed, and the effective date (since when it applies)    - Housing cooperative: A housing cooperative is a legal entity and a specific business corporation, established by at least 3 members primarily for the purpose of providing housing needs of its members, not for the purpose of doing business. It owns an apartment building and concludes lease agreements with its members for an indefinite period; members do not own the apartments directly, but have a cooperative share.



### 1.4 Future Modules (Phase 2+)### 1.2 Scope    - Association of Unit Owners: Unit Owners Association. This is a legal entity established for the purpose of managing, operating and repairing common parts of a house and land. All owners of apartments and non-residential premises in a given house are mandatory members of the SVJ.

The following modules are defined conceptually but will be designed and implemented later:

- **Financial Management** — fee collection, expense tracking, cost per project/repair/serviceUsers will be able to handle all tasks related to managing their property: building and flat registry, owner and tenant management, financial tracking, utility management, maintenance and repairs, communication, meetings, and document management. The system is designed as a set of **independent modules** that can be designed and implemented incrementally.

- **Utility Management** — meter readings, utility cost calculations per flat

- **Maintenance & Repairs** — repair requests, status tracking, scheduling, contractor management1. ### System Overview

- **Communication** — internal announcements, notifications (external website exists at https://www.bdsalounova.cz/)

- **Meetings & Voting** — meeting planning, minutes, resolutions, quorum tracking### 1.3 MVP Scope (Phase 1)- System Description

- **Document Management** — contracts, certificates, house rules, meeting minutes

The first version of the system focuses on the **core property registry**:1. ### Architectural Design

### 1.5 Definitions and Acronyms

- **Building management** — CRUD operations for buildings and their parameters- System Architecture Diagram

| Term | Definition |

|------|-----------|- **Flat management** — CRUD operations for flats/units and their parameters- Component Breakdown

| **Flat (Jednotka)** | An apartment unit within a building. Has parameters: area, number of rooms, layout, floor number, number of water and waste outlets, number of radiators and their power, gas installation status, balcony, cellar unit, unit ownership certificate number. |

| **Building (Budova)** | A physical structure containing flats. Has parameters: address, descriptive number (číslo popisné), indicative number (číslo orientační), floor plan, common rooms (laundry, drying room, bike room, workshop), number of floors, elevator, year built, total units, land plot number, rental of common areas. |- **Owner management** — CRUD operations for owners (natural or legal persons), including co-ownership- Technology Stack

| **Owner (Vlastník)** | A natural or legal person who owns a flat (in SVJ) or holds a cooperative share (in housing cooperative). One owner can own multiple flats. One flat can be owned by multiple owners (co-ownership). |

| **Tenant (Nájemník)** | A person renting a flat from its owner. One flat can have multiple tenants. The system tracks their contact information. |- **Tenant management** — CRUD operations for tenants, linked to flats and owners- Data Flow and Control Flow

| **SVJ (Společenství vlastníků jednotek)** | Association of Unit Owners. A legal entity established for managing, operating and repairing common parts of a house and land. All owners of apartments and non-residential premises are mandatory members. This is the primary legal model for this system. |

| **Housing Cooperative (Bytové družstvo)** | A legal entity and specific business corporation, established by at least 3 members primarily for providing housing needs. It owns the apartment building and concludes lease agreements with members; members do not own apartments directly but have a cooperative share. Supported as an alternative legal model. |- **Full audit trail** — Every change is recorded: who made it, when, what changed, and the effective date (since when it applies)

| **Administrator (Správce)** | The property manager responsible for the day-to-day operation of all buildings. There is one administrator for the entire property. Has full read/write access to all data. |

| **Board Member (Člen výboru)** | A member of the SVJ/cooperative governing board (5 members total). Has full read/write access. Can approve expenses and repair requests. |1. ### Detailed Design

| **Chairman (Předseda)** | The head of the board. Has all board member permissions plus special approval rights: approving repair requests, contracts above a defined monetary threshold. |

| **Individual Owner (Vlastník – uživatel)** | An owner accessing the system. Can view only their own relevant data (their flats, their financial records, their utility readings). Can submit requests (repair, data change) but cannot edit data directly. |### 1.4 Future Modules (Phase 2+)- [Component Name]

| **Audit Trail** | A complete history log of every data change: timestamp of change, who performed it, what field changed (old value → new value), and the effective date (since when the change applies in the real world). |

| **Effective Date (Platnost od)** | The real-world date from which a change applies (e.g., ownership transfer date), as opposed to the timestamp when the change was recorded in the system. |The following modules are defined conceptually but will be designed and implemented later:    - Responsibilities: [What does it do?]



---- **Financial Management** — fee collection, expense tracking, cost per project/repair/service    - Interfaces/APIs:



## 2. System Overview- **Utility Management** — meter readings, utility cost calculations per flat    - Inputs: [Describe input data.]



### 2.1 System Description- **Maintenance & Repairs** — repair requests, status tracking, scheduling, contractor management    - Outputs: [Describe output data.]

Solomon is a **web-based application** for managing a residential property complex consisting of 5 interconnected apartment buildings operated under a single SVJ (Společenství vlastníků jednotek) in the Czech Republic.

- **Communication** — internal announcements, notifications (external website exists at https://www.bdsalounova.cz/)    - Error Handling: [Describe approach.]

The system serves as the central tool for the property administrator, board members, and individual owners to manage all aspects of the property — from the physical registry of buildings and flats, through ownership and tenancy records, to financial tracking, maintenance, and communication.

- **Meetings & Voting** — meeting planning, minutes, resolutions, quorum tracking    - Data Structures: [Key models/schemas.]

### 2.2 User Personas

- **Document Management** — contracts, certificates, house rules, meeting minutes    - Algorithms/Logic: [Design patterns or important logic.]

#### Persona 1: Administrator (Správce)

- **Who:** The single property manager responsible for all 5 buildings    - State Management: [How is state handled?]

- **Goals:** Maintain accurate records of all buildings, flats, owners, and tenants. Track finances, coordinate repairs, manage utilities.

- **Access level:** Full read/write access to all data across all buildings and modules### 1.5 Definitions and Acronyms

- **Typical tasks:** Register new owner, update flat parameters, record meter readings, generate financial reports, manage repair requests

1. ### Database Design

#### Persona 2: Chairman (Předseda)

- **Who:** Head of the 5-member SVJ board| Term | Definition |ER Diagram / Schema Diagram:

- **Goals:** Oversee property management, approve significant decisions

- **Access level:** Full read/write access + special approval rights (repair requests, contracts above defined threshold)|------|-----------|Use Mermaid ER diagram here.

- **Typical tasks:** Approve large expenses, review repair requests, sign off on contracts, oversee board decisions

| **Flat (Jednotka)** | An apartment unit within a building. Has parameters: area, number of rooms, layout, floor number, number of water and waste outlets, number of radiators and their power, gas installation status, balcony, cellar unit, unit ownership certificate number. |Tables/Collections: [Define each with fields and constraints.]

#### Persona 3: Board Member (Člen výboru)

- **Who:** One of 5 members of the SVJ governing board| **Building (Budova)** | A physical structure containing flats. Has parameters: address, descriptive number (číslo popisné), indicative number (číslo orientační), floor plan, common rooms (laundry, drying room, bike room, workshop), number of floors, elevator, year built, total units, land plot number, rental of common areas. |Relationships: [Describe relationships between entities.]

- **Goals:** Participate in property management decisions, review data

- **Access level:** Full read/write access, can approve expenses and repair requests| **Owner (Vlastník)** | A natural or legal person who owns a flat (in SVJ) or holds a cooperative share (in housing cooperative). One owner can own multiple flats. One flat can be owned by multiple owners (co-ownership). |Migration Strategy: [If applicable.]

- **Typical tasks:** Review financial reports, approve repair requests, update property data

| **Tenant (Nájemník)** | A person renting a flat from its owner. One flat can have multiple tenants. The system tracks their contact information. |1. ### External Interfaces

#### Persona 4: Individual Owner (Vlastník)

- **Who:** An owner of one or more flats| **SVJ (Společenství vlastníků jednotek)** | Association of Unit Owners. A legal entity established for managing, operating and repairing common parts of a house and land. All owners of apartments and non-residential premises are mandatory members. This is the primary legal model for this system. |User Interface: [Mockups, UX notes.]

- **Goals:** View their own data, submit requests

- **Access level:** Read-only access to their own relevant data (their flats, their financial records). Can submit change requests and repair requests but cannot edit data directly.| **Housing Cooperative (Bytové družstvo)** | A legal entity and specific business corporation, established by at least 3 members primarily for providing housing needs. It owns the apartment building and concludes lease agreements with members; members do not own apartments directly but have a cooperative share. Supported as an alternative legal model. |External APIs: [Integrations and dependencies.]

- **Typical tasks:** View their flat details, check utility costs, submit a repair request, request a data change (e.g., new phone number — but the change must be confirmed by admin/board)

| **Administrator (Správce)** | The property manager responsible for the day-to-day operation of all buildings. There is one administrator for the entire property. Has full read/write access to all data. |Hardware Interfaces: [If any.]

### 2.3 Modular Architecture (Conceptual)

The system is composed of independent modules. Each module can be designed, implemented, and deployed separately. All modules share a common foundation.| **Board Member (Člen výboru)** | A member of the SVJ/cooperative governing board (5 members total). Has full read/write access. Can approve expenses and repair requests. |Network Protocols/Communication:



```| **Chairman (Předseda)** | The head of the board. Has all board member permissions plus special approval rights: approving repair requests, contracts above a defined monetary threshold. |[REST, GraphQL, gRPC, WebSockets, etc.]

┌─────────────────────────────────────────────────────────────────────┐

│                              SOLOMON                                │| **Individual Owner (Vlastník – uživatel)** | An owner accessing the system. Can view only their own relevant data (their flats, their financial records, their utility readings). Can submit requests (repair, data change) but cannot edit data directly. |1. ### Security Considerations

│                     Facility Management System                      │

├─────────────────────────────────────────────────────────────────────┤| **Audit Trail** | A complete history log of every data change: timestamp of change, who performed it, what field changed (old value → new value), and the effective date (since when the change applies in the real world). |Authentication: [Method used.]

│                                                                     │

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │| **Effective Date (Platnost od)** | The real-world date from which a change applies (e.g., ownership transfer date), as opposed to the timestamp when the change was recorded in the system. |Authorization: [Role/permission models.]

│  │  🏗 Building  │  │  🏠 Flat     │  │  👤 Owner    │  MVP        │

│  │  Management  │  │  Management  │  │  Management  │  (Phase 1)  │Data Protection: [Encryption, storage.]

│  └──────────────┘  └──────────────┘  └──────────────┘              │

│  ┌──────────────┐  ┌──────────────┐                                │---Compliance: [GDPR, HIPAA, etc.]

│  │  🧑 Tenant   │  │  📋 Audit    │                  MVP          │

│  │  Management  │  │  Trail       │                  (Phase 1)    │Threat Model:

│  └──────────────┘  └──────────────┘                                │

│                                                                     │## 2. System OverviewUse Mermaid diagram here if helpful.

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

│  │  💰 Financial│  │  🔧 Utility  │  │  🛠 Mainten. │  Future     │1. ### Performance and Scalability

│  │  Management  │  │  Management  │  │  & Repairs   │  (Phase 2+) │

│  └──────────────┘  └──────────────┘  └──────────────┘              │### 2.1 System DescriptionExpected Load: [Requests per second, data volume.]

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

│  │  📢 Communi- │  │  🗳 Meetings │  │  📄 Document │  Future     │The Facility Management System is a **web-based application** for managing a residential property complex consisting of 5 interconnected apartment buildings operated under a single SVJ (Společenství vlastníků jednotek) in the Czech Republic.Caching Strategy: [Describe caches used.]

│  │  cation      │  │  & Voting    │  │  Management  │  (Phase 2+) │

│  └──────────────┘  └──────────────┘  └──────────────┘              │Database Optimization: [Indexes, partitioning.]

│                                                                     │

├─────────────────────────────────────────────────────────────────────┤The system serves as the central tool for the property administrator, board members, and individual owners to manage all aspects of the property — from the physical registry of buildings and flats, through ownership and tenancy records, to financial tracking, maintenance, and communication.Scaling Strategy: [Vertical/horizontal.]

│  🔐 Authentication & Authorization │ 🌍 Localization (CZ primary) │

│  📝 Audit Trail Engine             │ 🔔 Notification Engine        │1. ### Deployment Architecture

├─────────────────────────────────────────────────────────────────────┤

│                    Shared Foundation / Common Services               │### 2.2 User PersonasEnvironments: [Dev, staging, production.]

└─────────────────────────────────────────────────────────────────────┘

```CI/CD Pipeline: [Tools and stages.]



### 2.4 Key System Characteristics#### Persona 1: Administrator (Správce)Infrastructure Diagram:

- **Multi-building:** Supports 5 buildings under one SVJ, extensible

- **Single management entity:** One administrator, one board (5 members + chairman)- **Who:** The single property manager responsible for all 5 buildingsUse Mermaid diagram here.

- **Multi-language:** Localization support with Czech as the primary language

- **Full audit trail:** Every data change is tracked with user, timestamp, diff, and effective date- **Goals:** Maintain accurate records of all buildings, flats, owners, and tenants. Track finances, coordinate repairs, manage utilities.Cloud/Hosting: [AWS, GCP, Azure, etc.]

- **Role-based access:** Four distinct roles with different permissions

- **Modular:** Independent modules that can be built incrementally- **Access level:** Full read/write access to all data across all buildings and modulesContainerization/Orchestration: [Docker, Kubernetes.]

- **Czech legal context:** Designed for SVJ (primary) with housing cooperative as alternative

- **Typical tasks:** Register new owner, update flat parameters, record meter readings, generate financial reports, manage repair requests10. Testing Strategy

---

Unit Testing: [Tools, coverage goals.]

## 3. Architectural Design

#### Persona 2: Chairman (Předseda)Integration Testing: [Approach and tools.]

### 3.1 Technology Stack

- **Who:** Head of the 5-member SVJ boardEnd-to-End Testing: [Scope and tools.]

#### 3.1.1 Recommendation: Django (Python) — Full-Stack Monolith

- **Goals:** Oversee property management, approve significant decisionsQuality Metrics: [Code coverage, linting, etc.]

After analyzing the project requirements, the recommended technology stack is:

- **Access level:** Full read/write access + special approval rights (repair requests, contracts above defined threshold)11. Appendices

| Layer | Technology | Rationale |

|-------|-----------|-----------|- **Typical tasks:** Approve large expenses, review repair requests, sign off on contracts, oversee board decisionsDiagrams: [All referenced diagrams.]

| **Backend + Frontend** | **Django** (Python) | Full-stack web framework with built-in admin, ORM, auth, localization, and audit capabilities. Perfect for data-driven CRUD applications. |

| **Database** | **PostgreSQL** | Robust relational database. Required for M:N relationships, temporal data, audit trail. Free on most hosting. |Glossary: [Terms and definitions.]

| **Frontend Enhancement** | **Django Templates + HTMX** | Server-rendered HTML with HTMX for dynamic interactions without JavaScript complexity. Clean, fast, maintainable. |

| **CSS Framework** | **Tailwind CSS** or **Bootstrap 5** | Responsive design out of the box. No designer needed. |#### Persona 3: Board Member (Člen výboru)Change History:

| **Localization** | **Django i18n** (built-in) | Django has first-class internationalization support. Czech translations built-in. |

| **Audit Trail** | **django-auditlog** or **django-simple-history** | Mature packages that automatically track all model changes with user, timestamp, old/new values. |- **Who:** One of 5 members of the SVJ governing board[Version, Date, Author, Changes]

- **Goals:** Participate in property management decisions, review data

#### 3.1.2 Why Django over React.js?- **Access level:** Full read/write access, can approve expenses and repair requests

- **Typical tasks:** Review financial reports, approve repair requests, update property data

| Criteria | Django (recommended) | React.js + API backend |

|----------|---------------------|----------------------|#### Persona 4: Individual Owner (Vlastník)

| **Complexity** | ⭐ Single codebase, one language (Python) | ❌ Two separate apps (React frontend + API backend), two languages |- **Who:** An owner of one or more flats

| **Admin interface** | ⭐ Built-in Django Admin — ready-made CRUD for all models, free | ❌ Must build every admin screen from scratch |- **Goals:** View their own data, submit requests

| **Audit trail** | ⭐ Mature Django packages (django-auditlog) handle this automatically | ❌ Must implement manually in the API layer |- **Access level:** Read-only access to their own relevant data (their flats, their financial records). Can submit change requests and repair requests but cannot edit data directly.

| **Localization** | ⭐ Django i18n is built-in, battle-tested, supports Czech | ⚠️ Must set up i18next or similar, more configuration |- **Typical tasks:** View their flat details, check utility costs, submit a repair request, request a data change (e.g., new phone number — but the change must be confirmed by admin/board)

| **Authentication** | ⭐ Built-in user/group/permission system | ❌ Must implement or integrate (e.g., Auth0, NextAuth) |

| **Development speed** | ⭐ One developer can build the full MVP quickly | ❌ Need frontend + backend expertise, more code to write |### 2.3 Modular Architecture (Conceptual)

| **Hosting cost** | ⭐ Simple deployment, works on cheap shared hosting or VPS | ⚠️ Needs Node.js hosting for frontend + separate API server |The system is composed of independent modules. Each module can be designed, implemented, and deployed separately. All modules share a common foundation.

| **Maintenance** | ⭐ Single deployment, single stack to maintain | ❌ Two deployments, two dependency trees, more complexity |

| **User experience** | ⚠️ Server-rendered, but HTMX makes it feel snappy | ⭐ Rich SPA experience, but overkill for this app |```

┌─────────────────────────────────────────────────────────────────────┐

**Verdict:** React.js is excellent for complex, highly interactive frontends (e.g., real-time dashboards, drag-and-drop interfaces). Solomon is primarily a **data management application** with CRUD forms, tables, and reports — Django's sweet spot. Adding HTMX gives Django apps a modern, responsive feel without the complexity of a full JavaScript framework.│                        FACILITY MANAGEMENT SYSTEM                   │

├─────────────────────────────────────────────────────────────────────┤

> **Note:** If in the future a rich interactive feature is needed (e.g., a drag-and-drop floor plan editor), a React component can be embedded into a Django page for just that feature.│                                                                     │

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

#### 3.1.3 Why Not a Separate Frontend?│  │  🏗 Building  │  │  🏠 Flat     │  │  👤 Owner    │  MVP        │

│  │  Management  │  │  Management  │  │  Management  │  (Phase 1)  │

For Solomon specifically:│  └──────────────┘  └──────────────┘  └──────────────┘              │

- **~200 users**, low traffic, simple CRUD — no need for SPA complexity│  ┌──────────────┐  ┌──────────────┐                                │

- **One developer** (or small team) — maintaining one codebase is significantly easier│  │  🧑 Tenant   │  │  📋 Audit    │                  MVP          │

- **Audit trail and permissions** — Django handles this out of the box│  │  Management  │  │  Trail       │                  (Phase 1)    │

- **Speed to MVP** — Django Admin alone gives you a working admin interface in days│  └──────────────┘  └──────────────┘                                │

- **HTMX** bridges the gap — dynamic forms, inline editing, live search without a single line of React│                                                                     │

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

### 3.2 Hosting Analysis│  │  💰 Financial│  │  🔧 Utility  │  │  🛠 Mainten. │  Future     │

│  │  Management  │  │  Management  │  │  & Repairs   │  (Phase 2+) │

#### 3.2.1 Comparison of Hosting Options│  └──────────────┘  └──────────────┘  └──────────────┘              │

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │

| Option | Monthly Cost | Pros | Cons | Verdict |│  │  📢 Communi- │  │  🗳 Meetings │  │  📄 Document │  Future     │

|--------|-------------|------|------|---------|│  │  cation      │  │  & Voting    │  │  Management  │  (Phase 2+) │

| **Google Cloud Run (free tier)** | **~0 CZK** (free tier) | 2M requests/month free, auto-scales to zero, EU region (europe-west1), PostgreSQL free trial 90 days | PostgreSQL costs ~$7–10/month after trial. Requires Docker knowledge. Not truly free long-term for DB. | ⚠️ Good for experimentation, not truly free for production |│  └──────────────┘  └──────────────┘  └──────────────┘              │

| **Google Cloud e2-micro** | **~0 CZK** (always free) | 1 free e2-micro VM, always free, 30 GB disk | Only US regions (not EU = GDPR concern). Very limited resources (0.25 vCPU, 1 GB RAM). Must manage everything yourself. | ❌ GDPR issue, too weak |│                                                                     │

| **Railway.com (Hobby)** | **~$5/month (~120 CZK)** | Deploy from GitHub, PostgreSQL included, automatic HTTPS, very easy setup | Limited to 0.5 GB RAM on free, custom domain costs extra on free plan | ⭐ Excellent for MVP/development |├─────────────────────────────────────────────────────────────────────┤

| **Hukot.net (VPS)** | **~100–200 CZK/month** | Czech hosting, Czech support, GDPR compliant, VPS with full control, PostgreSQL supported | Must manage server yourself (updates, security) | ⭐ Good for production, Czech-based |│  🔐 Authentication & Authorization │ 🌍 Localization (CZ primary) │

| **WEDOS/VEDOS (shared hosting)** | **~50–100 CZK/month** | Cheapest Czech option, Czech datacenters, GDPR ready | Shared hosting = PHP only, **no Python/Django support**. Would need WordPress or PHP framework. | ❌ Not suitable for Django |│  📝 Audit Trail Engine             │ 🔔 Notification Engine        │

| **Fly.io** | **~0–$5/month** | Free tier with 3 shared VMs, PostgreSQL included, EU regions available | Free tier is very limited. Company is US-based. | ⚠️ Possible but limited |├─────────────────────────────────────────────────────────────────────┤

| **DigitalOcean App Platform** | **~$5/month (~120 CZK)** | EU regions (Amsterdam), easy deployment, managed database add-on | DB add-on costs extra ($7/month) | ⚠️ Good but adds up |│                    Shared Foundation / Common Services               │

└─────────────────────────────────────────────────────────────────────┘

#### 3.2.2 Recommended Hosting Strategy```



**Phase 1 (Development & MVP): Railway.com — Hobby plan ($5/month)**### 2.4 Key System Characteristics

- Deploy directly from GitHub repository- **Multi-building:** Supports 5 buildings under one SVJ, extensible

- PostgreSQL database included- **Single management entity:** One administrator, one board (5 members + chairman)

- Automatic HTTPS, custom domain support- **Multi-language:** Localization support with Czech as the primary language

- Zero server management — just push code- **Full audit trail:** Every data change is tracked with user, timestamp, diff, and effective date

- Perfect for getting the MVP running quickly- **Role-based access:** Four distinct roles with different permissions

- **Modular:** Independent modules that can be built incrementally

**Phase 2 (Production): Hukot.net — VPS (~150 CZK/month)**- **Czech legal context:** Designed for SVJ (primary) with housing cooperative as alternative

- Czech hosting, servers in Czech Republic → full GDPR compliance

- Full control over the server (Ubuntu + Docker or direct install)---

- PostgreSQL, backups, enough resources for 200 users

- Czech-language support, local company## 3. Architectural Design

- Long-term stable and affordable

### 3.1 Component Breakdown

**Why not free hosting for production?**

- Google Cloud free tier is US-only (GDPR concern for Czech personal data)#### 3.1.1 Foundation Layer (shared by all modules)

- Free tiers are unreliable for production (resource limits, cold starts, no SLA)| Component | Responsibility |

- Solomon handles personal data (GDPR) — you need a hosting provider that is GDPR compliant with EU-based servers|-----------|---------------|

- At ~150 CZK/month (~$6), a Czech VPS is extremely affordable and appropriate for an SVJ| **Auth & Identity** | User registration, login, session management, role assignment |

| **Authorization Engine** | Permission checks based on role (Admin, Chairman, Board Member, Owner) and data ownership |

#### 3.2.3 Cost Summary| **Audit Trail Engine** | Intercepts all data modifications, records: user, timestamp, entity, field, old value, new value, effective date |

| **Localization Service** | Manages translations, date/currency/number formatting for Czech locale (and future languages) |

| Phase | Hosting | Database | Domain | Total || **Notification Engine** | Sends notifications (in-app, email) triggered by events (new request, approval needed, change recorded) |

|-------|---------|----------|--------|-------|

| Development | Railway Hobby ($5) | Included | — | **~$5/month (120 CZK)** |#### 3.1.2 MVP Modules (Phase 1)

| Production | Hukot VPS (~150 CZK) | Included (self-hosted PostgreSQL) | solomon.bdsalounova.cz (~0, subdomain) | **~150 CZK/month** |

**Module: Building Management (Správa budov)**

### 3.3 Component Breakdown| Aspect | Description |

|--------|-------------|

#### 3.3.1 Foundation Layer (shared by all modules)| Responsibilities | Create, read, update, (soft-)delete buildings and their parameters |

| Component | Responsibility || Key data | Address, descriptive number, indicative number, floor plan, common rooms, number of floors, elevator (yes/no), year built, total units, land plot number, rental of common areas |

|-----------|---------------|| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only, their buildings) |

| **Auth & Identity** | User registration, login, session management, role assignment || Business rules | Deleting a building soft-deletes it (kept for history). All changes tracked via audit trail. |

| **Authorization Engine** | Permission checks based on role (Admin, Chairman, Board Member, Owner) and data ownership |

| **Audit Trail Engine** | Intercepts all data modifications, records: user, timestamp, entity, field, old value, new value, effective date |**Module: Flat Management (Správa bytových jednotek)**

| **Localization Service** | Manages translations, date/currency/number formatting for Czech locale (and future languages) || Aspect | Description |

| **Notification Engine** | Sends notifications (in-app, email) triggered by events (new request, approval needed, change recorded) ||--------|-------------|

| Responsibilities | Create, read, update, (soft-)delete flats and their parameters. Link flats to buildings. |

#### 3.3.2 MVP Modules (Phase 1)| Key data | Area, number of rooms, layout, floor number, water outlets count, waste outlets count, number of radiators, radiator power, gas installed (yes/no), balcony (yes/no), cellar unit, unit ownership certificate number |

| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only, their flats) |

**Module: Building Management (Správa budov)**| Business rules | Each flat belongs to exactly one building. A flat can have multiple owners and multiple tenants. All changes tracked. |

| Aspect | Description |

|--------|-------------|**Module: Owner Management (Správa vlastníků)**

| Responsibilities | Create, read, update, (soft-)delete buildings and their parameters || Aspect | Description |

| Key data | Address, descriptive number, indicative number, floor plan, common rooms, number of floors, elevator (yes/no), year built, total units, land plot number, rental of common areas ||--------|-------------|

| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only, their buildings) || Responsibilities | Create, read, update, (soft-)delete owners. Link owners to flats. Manage co-ownership. |

| Business rules | Deleting a building soft-deletes it (kept for history). All changes tracked via audit trail. || Key data | Name (natural or legal person), permanent address, contact address, phone, email, deputy/representative, ownership share size, move-in date, notes |

| Users | Administrator, Board Members (full CRUD); Individual Owners (read-only for their own record, can submit change requests) |

**Module: Flat Management (Správa bytových jednotek)**| Business rules | One owner can own multiple flats (1:N). One flat can have multiple owners — co-ownership (M:N) with share sizes. Ownership share is expressed as a fraction/percentage. Ownership changes must have an effective date. |

| Aspect | Description |

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
