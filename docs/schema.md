# Relational CSV Structure for ISO 19115-2 / NCEI Metadata

**Document Type:** Architecture Standard & Compliance Guidelines
**Target Standards:** ISO 19115-2, NCEI Archival Rubric, OGC SensorThings (Conceptual)

## 1. Architectural Principles and Normative Rules

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

This standard utilizes an Event-Driven relational model distributed across seven CSV tables, linked by exact, descriptive engineering headers (e.g., `event_id`). 

### 1.1 Record Granularity and Hierarchy
* **Granularity:** Implementations SHALL generate a discrete ISO 19115-2 record for every event node. Top-level nodes (no parent) map to `MD_ScopeCode="project"` or `"series"`. Leaf nodes map to `MD_ScopeCode="dataset"`.
* **Inheritance:** "Skinny Child" leaf events MAY omit heavy descriptive fields (e.g., Contacts, Abstracts). Compiling pipelines MUST resolve missing mandatory fields by walking up the `parent_event_id` chain and inheriting values from the nearest populated ancestor.

### 1.2 Geometry and Temporal Rules
* **CRS:** All spatial coordinates MUST be expressed in WGS84 (EPSG:4326) with a Longitude/Latitude axis order. 
* **Bounding Boxes:** Pipelines SHALL derive ISO 19115 bounding boxes from the provided `geometry` Well-Known Text (WKT). Implementations MUST correctly calculate boxes crossing the antimeridian.
* **Ongoing Events:** If an event is currently active, `end_time` MAY be left NULL, resolving to a nil reason of "unknown" or "ongoing" in the resulting ISO XML.

### 1.3 Data Payload Separation
This metadata schema defines *discovery metadata*. Data payloads (e.g., self-describing NetCDF files, STAC Catalogs for imagery) SHALL NOT be stored within these tables. They MUST be referenced via the `Related_Entities.csv` network table.

---

## 2. Schema Definitions

### 2.1 Events.csv (The Core Tree)
*Establishes the hierarchy, timing, and spatial footprint. One distinct platform operation = one event.*

| CSV Header | Target Standard / Ontology | Requirement Level | Description |
| ----- | ----- | ----- | ----- |
| `event_id` | `dc:identifier` / `MD_Identifier` | **MUST** | Primary Key. Unique UUID for this specific event node. |
| `parent_event_id` | `dcterms:isPartOf` / `parentIdentifier` | **OPTIONAL** | Foreign Key to parent event. Null for root nodes. |
| `event_type` | `dc:type` / `MI_Operation` | **MUST** | Event category (e.g., `Cruise`, `Drop Site`, `UAV Flight`). |
| `event_name` | `dc:title` | **MUST** | Human-readable name or local code (e.g., "Pac-Geo-01"). |
| `abstract` | `dcterms:abstract` | **MUST (Ancestry)** | Plain-language executive summary. |
| `purpose` | `acdd:purpose` | **RECOMMENDED** | Scientific rationale or funding purpose. |
| `start_time` | `acdd:time_coverage_start` | **MUST** | Time period begin (Strict ISO 8601). |
| `end_time` | `acdd:time_coverage_end` | **MUST** | Time period end (Strict ISO 8601). |
| `geometry` | `locn:geometry` / `EX_Extent` | **MUST** | WKT representing the footprint (WGS84). |

### 2.2 Contacts.csv (The People & Organizations)
*ISO 19115-2 requires distinct roles and comprehensive contact info, necessitating a dedicated table.*

| CSV Header | Target Standard / Ontology | Requirement Level | Description |
| ----- | ----- | ----- | ----- |
| `event_id` | `dcterms:isPartOf` | **MUST** | Foreign Key to `Events.csv`. |
| `contact_name` | `acdd:creator_name` / `CI_ResponsibleParty` | **RECOMMENDED** | Name of the person (if applicable). |
| `organization` | `acdd:creator_institution` | **MUST** | Name of the responsible organization. |
| `email` | `acdd:creator_email` | **MUST** | Contact email address. |
| `role` | `CI_RoleCode` | **MUST** | ISO role (e.g., `principalInvestigator`, `pointOfContact`, `custodian`). |
| `orcid` | `dc:identifier` | **RECOMMENDED** | ORCID or ROR URL for the contact/org. |

### 2.3 Platforms.csv (The Vehicles / "Things")
*Tracks the physical vehicles. Utilizes global registries (e.g., ICES, IMO) rather than local UUID primary keys.*

| CSV Header | Target Standard / Ontology | Requirement Level | Description |
| ----- | ----- | ----- | ----- |
| `event_id` | `dcterms:isPartOf` | **MUST** | Foreign Key to `Events.csv`. |
| `platform_identifier`| `dc:identifier` / `MI_Platform` | **MUST** | Code from a recognized global registry. |
| `identifier_type` | `dc:type` | **MUST** | The registry used (e.g., `ICES`, `IMO`, `Local`). |
| `platform_name` | `dc:title` | **MUST** | Human-readable name (e.g., "R/V Atlantis"). |
| `platform_type` | `acdd:platform` | **RECOMMENDED** | Make/Model/Class of the vehicle. |

### 2.4 Sensors.csv (The Instruments)
*Tracks specific measurement devices used during the event.*

| CSV Header | Target Standard / Ontology | Requirement Level | Description |
| ----- | ----- | ----- | ----- |
| `sensor_id` | `dc:identifier` | **MUST** | Primary Key for this deployment instance of the sensor. |
| `event_id` | `dcterms:isPartOf` | **MUST** | Foreign Key to `Events.csv`. |
| `sensor_name` | `dc:title` / `MI_Instrument` | **MUST** | Human-readable name (e.g., "SBE 911plus"). |
| `instrument_type` | `acdd:instrument` | **RECOMMENDED** | Broad type category (e.g., "CTD"). |
| `vocabulary` | `acdd:instrument_vocabulary`| **RECOMMENDED** | Standard vocabulary used for the type. |

### 2.5 Variables.csv (The Datastream / "ObservedProperty")
*Tracks scientific measurements. Directly linked to the Sensor that measured it to preserve data lineage.*

| CSV Header | Target Standard / Ontology | Requirement Level | Description |
| ----- | ----- | ----- | ----- |
| `sensor_id` | `dcterms:isPartOf` | **MUST** | Foreign Key to `Sensors.csv`. |
| `variable_name` | `cf:standard_name` / `MD_Band` | **MUST** | Short standard name (e.g., "sea_water_temperature"). |
| `variable_desc` | `dc:description` | **MUST** | Long-form description as required by NCEI. |
| `unit_of_measure`| `qudt:unit` | **MUST** | Physical unit (e.g., "Celsius", "meter"). |

### 2.6 Keywords.csv (The Vocabulary)
*Handles thematic, spatial, and organizational discoverability.*

| CSV Header | Target Standard / Ontology | Requirement Level | Description |
| ----- | ----- | ----- | ----- |
| `event_id` | `dcterms:isPartOf` | **MUST** | Foreign Key to `Events.csv`. |
| `keyword_type` | `MD_KeywordTypeCode` | **MUST** | ISO category (e.g., `theme`, `place`, `stratum`). |
| `vocabulary` | `acdd:keyword_vocabulary` | **MUST** | Thesaurus used (e.g., "GCMD Science Keywords"). |
| `keyword` | `dc:subject` | **MUST** | The exact hierarchical keyword string. |

### 2.7 Related_Entities.csv (The Network)
*Links external context and provides direct data access endpoints (e.g., NetCDF files, STAC Catalogs).*

| CSV Header | Target Standard / Ontology | Requirement Level | Description |
| ----- | ----- | ----- | ----- |
| `event_id` | `dcterms:isPartOf` | **MUST** | Foreign Key to `Events.csv`. |
| `relation_type` | `dc:relation` / `CI_RoleCode` | **MUST** | Standard link type (e.g., `isRelatedTo`, `download`). |
| `entity_title` | `dc:title` | **RECOMMENDED** | Name of the project, dataset, or paper. |
| `entity_url` | `dc:source` / `CI_OnlineResource`| **RECOMMENDED** | Direct URL to the entity/payload. |
| `entity_id` | `dc:identifier` | **OPTIONAL** | External machine key (DOI, Grant ID). |
