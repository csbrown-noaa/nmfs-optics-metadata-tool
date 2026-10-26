# Site-Level Relational CSV Metadata Schema Specification

**Document Type:** Architecture Standard & Compliance Guidelines
**Target Standard:** ISO 19115-2:2009 (via ISO 19139 XML encoding)
**Target Archives:** NOAA NCEI
**Scope:** Single-Cruise Field Operations (Leaf Nodes / Datasets)

## 1. Architectural Principles and Normative Rules

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

This specification dictates a streamlined, 5-table relational CSV model designed specifically to capture granular field operations (e.g., Drop Sites, Transects, Dives).

### 1.1. The "Single Cruise" InPort Integration

This schema represents a **flat list of leaf-node events** belonging to a single overarching deployment (e.g., a specific Cruise or Leg).

* **Out-of-Band Parents:** This schema DOES NOT record overarching project narrative, administrative contacts, overarching keywords, or licensing. Implementers SHALL assume that an authoritative, fully compliant ISO 19115-2 XML record (e.g., generated via NOAA InPort) is provided at ETL execution time to act as the overarching Series/Project parent.

* **No CSV Hierarchy:** Because a batch of CSVs maps directly to one supplied Parent XML, internal hierarchical routing (e.g., `parent_event_id`) is omitted. Every row in `Events.csv` attaches directly to the provided Parent.

### 1.2. CSV Mechanical Conventions

* **Encoding:** All CSV files MUST be encoded in UTF-8.

* **Separators & Escaping:** The delimiter is a comma (`,`). Fields containing commas (especially WKT geometries) MUST be enclosed in double quotes (`"`).

* **Null Values:** Missing or empty values MUST be represented as an empty string (no characters between commas).

* **Identifiers:** All Primary/Foreign Keys MUST be valid UUIDs (v4 recommended).

### 1.3. Explicit Abstract and Event Independence

To ensure database integrity and eliminate complex inheritance assumptions, every row in the CSV MUST be self-contained for its descriptive payload. A child event MUST explicitly define its own `abstract` (e.g., "CTD cast at Drop Site Alpha during Cruise Pac-Geo-01").

### 1.4. Geometry and Temporal Rules

* **CRS and Axis:** Spatial coordinates MUST use WGS84 (EPSG:4326) with a Longitude/Latitude axis order.

* **WKT Format:** Footprints MUST be provided as Well-Known Text (e.g., `POINT (lon lat)`, `LINESTRING(lon lat, lon lat)`).

* **Bounding Boxes:** Downstream XML builders SHALL derive ISO bounding boxes from the WKT. If the geometry crosses the antimeridian, it MUST be represented with `westBoundLongitude` > `eastBoundLongitude`.

* **Ongoing Events:** If an event is currently active, `end_time` MAY be NULL. XML builders SHALL translate this to `indeterminatePosition="now"`.

## 2. Schema Definitions

*Requirement tags denote the justification for inclusion: **\[System\]** = Relational integrity; **\[ISO\]** = ISO 19115 core mandate; **\[NCEI\]** = NCEI Archival Rubric mandate.*

### 2.1 Events.csv (The Field Operations Manifest)

*A flat list of discrete operations (Drop Sites, Transects) performed during the cruise.*

| CSV Header | Target Ontology / XML Element | Requirement | Description | 
| ----- | ----- | ----- | ----- | 
| `event_id` | `gmd:fileIdentifier` | **MUST** \[System\] | Primary Key. Unique UUID for this operation. | 
| `event_type` | `dc:type` / `gmi:MI_Operation` | **MUST** \[ISO\] | Operation category (e.g., `Drop Site`, `Transect`). Scope resolves to `dataset`. | 
| `event_name` | `dc:title` / `gmd:title` | **MUST** \[ISO\] | Human-readable local code (e.g., "CTD Cast 01"). | 
| `abstract` | `dcterms:abstract` | **MUST** \[ISO\] | Explicit, plain-language summary of the specific operation. | 
| `start_time` | `acdd:time_coverage_start` | **MUST** \[ISO\] | ISO 8601 Timestamp (UTC). | 
| `end_time` | `acdd:time_coverage_end` | **CONDITIONAL** | ISO 8601 Timestamp (UTC). MUST exist unless ongoing. | 
| `geometry` | `locn:geometry` | **MUST** \[ISO\] | WGS84 WKT footprint. | 

### 2.2 Platforms.csv (The Vehicles)

*Tracks the physical vehicles (Ships, AUVs, UAVs) deployed for a specific event.*

| CSV Header | Target Ontology / XML Element | Requirement | Description | 
| ----- | ----- | ----- | ----- | 
| `platform_id` | System Key | **MUST** \[System\] | Primary Key for this deployment record. | 
| `event_id` | `dc:identifier` | **MUST** \[System\] | Foreign Key to Events.csv. | 
| `platform_name` | `acdd:platform` | **MUST** \[NCEI\] | Human-readable name (e.g., "R/V Atlantis", "AUV Sentry"). | 
| `platform_identifier` | `dc:identifier` | **RECOMMENDED** | Code from a global registry (e.g., ICES, IMO). | 
| `identifier_type` | Vocabulary Name | **RECOMMENDED** | Registry namespace (e.g., `ICES`, `Local`). | 

### 2.3 Sensors.csv (The Instruments)

*Tracks specific measurement devices used during the event.*

Recommend using [SeaDataNet L22](https://vocab.seadatanet.org/v_bodc_vocab_v2/browse.asp?order=conceptid&formname=search&screen=0&lib=l22&v0_0=ctd&v1_0=conceptid%2Cpreflabel%2Caltlabel%2Cdefinition%2Cmodified&v2_0=0&v0_1=&v1_1=conceptid&v2_1=3&v0_2=&v1_2=preflabel&v2_2=3&v0_3=&v1_3=altlabel&v2_3=3&v0_4=&v1_4=modified&v2_4=9&v0_5=&v1_5=modified&v2_5=10&x=0&y=0&v1_6=&v2_6=&v1_7=&v2_7=) for `sensor_name`.

Recommend using [GCMD keywords](https://gkv-keyword.earthdatacloud.nasa.gov/scheme/all/01cc0beb-7c9a-40ed-ad86-0661b41aee53?gtm_keyword=CTD&gtm_scheme=instruments) for `instrument_type`.

| CSV Header | Target Ontology / XML Element | Requirement | Description | 
| ----- | ----- | ----- | ----- | 
| `sensor_id` | System Key | **MUST** \[System\] | Primary Key. | 
| `event_id` | `dc:identifier` | **MUST** \[System\] | Foreign Key to Events.csv. | 
| `sensor_name` | `acdd:instrument` | **MUST** \[NCEI\] | Human-readable name (e.g., "Sea-Bird SBE 911plus"). | 
| `instrument_type` | `gmi:type` | **RECOMMENDED** | Broad type category (e.g., "CTD", "Camera"). | 

### 2.4 Variables.csv (The Measurements)

*Tracks the scientific parameters contained in the dataset. Links to Sensors for observational data.*

| CSV Header | Target Ontology / XML Element | Requirement | Description | 
| ----- | ----- | ----- | ----- | 
| `variable_id` | System Key | **MUST** \[System\] | Primary Key. | 
| `event_id` | `dc:identifier` | **MUST** \[System\] | Foreign Key to Events.csv. | 
| `sensor_id` | System Key | **OPTIONAL** | Foreign Key to Sensors.csv. Null if data is derived/modeled. | 
| `variable_name` | `dc:title` | **MUST** \[NCEI\] | Local parameter name. | 
| `cf_standard_name` | `cf:standard_name` | **RECOMMENDED** | CF Standard Name (if applicable). | 
| `description` | `dc:description` | **MUST** \[NCEI\] | NCEI-mandated description of what the parameter represents. | 
| `unit_of_measure` | `qudt:unit` | **MUST** \[NCEI\] | UDUNITS or UCUM string (e.g., `Celsius`, `m/s`). | 

### 2.5 Related_Entities.csv (The Payload & Network Links)

*Holds external context and data retrieval URIs. If `url` is populated, it maps to a Data/Download Link (`CI_OnlineResource`). If `external_identifier` is populated with no URL, it maps to an Aggregated Resource (`MD_AggregateInformation`).*

| CSV Header | Target Ontology / XML Element | Requirement | Description | 
| ----- | ----- | ----- | ----- | 
| `entity_id` | System Key | **MUST** \[System\] | Primary Key. | 
| `event_id` | `dc:identifier` | **MUST** \[System\] | Foreign Key to Events.csv. | 
| `relation_type` | `dc:relation_type` | **MUST** \[ISO\] | Defines the linkage (e.g., `download`, `stac_catalog`, `isReferencedBy`). | 
| `title` | `dc:title` | **MUST** \[ISO\] | Name of the payload or resource. | 
| `url` | `dc:source` | **CONDITIONAL** | Target URI. MUST be populated for data download payloads. | 
| `external_identifier` | `dc:identifier` | **CONDITIONAL** | External registry key (e.g., DOI, Grant ID). | 

