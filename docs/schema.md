## 1. Architectural Overview

This specification dictates the relational schema for generating standard-compliant ISO 19115-2 XML metadata. The architecture employs an "Event-Driven" relational model, heavily inspired by OGC SensorThings and ISO 19115-2. Data is distributed across six CSVs linked by a common UUID. This allows for arbitrary field hierarchies (e.g., Survey -> Cruise -> Deployment -> Site).

To ensure database clarity and interoperability, CSV headers utilize exact, descriptive terms (e.g., `event_id`). A crosswalk to standard vocabularies—such as Dublin Core (dc/dcterms), Attribute Convention for Data Discovery (acdd), and the Location Core Vocabulary (locn)—is explicitly mapped in the schema definitions below.

### 1.1 Compliance and Validation Mandates

To achieve baseline validation and successful archival ingestion, specific fields must be populated. The schema distinguishes between system-level requirements (necessary for relational integrity) and archival requirements (necessary for NCEI to accept the XML).

* **ISO 19115-2 Mandates:** Strictly requires a spatial bounding box, a temporal bounding box, and at least one topical keyword.
* **NCEI Archival Mandates:** The NCEI Rubric expands upon ISO baselines, requiring an explicit abstract, at least one Point of Contact (Creator), platform/instrument descriptions for observational data, and variable (measured parameter) definitions.
* **Inheritance Principle ("Heavy Parent, Skinny Child"):** Mandatory fields such as Abstract and Point of Contact are only strictly required at the **Parent Event** level. Child events may leave these fields null (`NULL`); downstream Extract-Transform-Load (ETL) pipelines shall walk up the `parent_event_id` chain to inherit parent values.

### 1.2 Data vs. Metadata Separation (The STAC & NetCDF Paradigm)

This schema strictly defines *discovery metadata*. Item-level data payloads shall not be stored here.

* **Continuous/Discrete Numerical Data:** Recommend that these be stored as self-describing NetCDF files.
* **Extensive Visual Data (Video/Imagery):** Recommend that image and video manifests be managed via a SpatioTemporal Asset Catalog (STAC).
* **Integration:** The ISO 19115-2 records generated from this schema shall act as the central hub, utilizing the `Related_Entities.csv` to provide high-level endpoint URLs pointing to the overarching data files.

## 2. Schema Definitions

### 2.1 Events.csv (The Core Tree)

*This table establishes the hierarchy, timing, spatial footprint, and overarching project details. For "Skinny Child" sites, the heavy fields (Abstract, Purpose, POCs) can be left blank (NULL); the generation script will inherit them. Rule of thumb: One platform operation = one event.*

| CSV Header | Description | Ontology Mapping | Requirement Level | 
| ----- | ----- | ----- | ----- |
| `event_id` | **PRIMARY KEY:** Unique UUID for this specific event node. | `dc:identifier` | **SYSTEM MANDATORY** | 
| `parent_event_id` | **FOREIGN KEY:** UUID of the parent event. Leave blank for top-level nodes. | `dcterms:isPartOf` | OPTIONAL (Null for Root) | 
| `event_type` | Event category (e.g., `Survey`, `Cruise`, `Deployment`, `Drop Site`). | `dc:type` | **ARCHIVAL MANDATORY** | 
| `event_name` | Human-readable name or local code (e.g., "Pac-Geo-01"). | `dc:title` | **ARCHIVAL MANDATORY** | 
| `abstract` | *(Heavy Field)* Plain-language executive summary. | `dcterms:abstract` | **ARCHIVAL MANDATORY (Parent)** | 
| `purpose` | *(Heavy Field)* Scientific rationale or funding purpose. | `acdd:purpose` | RECOMMENDED | 
| `poc_name` | *(Heavy Field)* Name of the primary Point of Contact (POC). | `acdd:creator_name` | **ARCHIVAL MANDATORY (Parent)** | 
| `start_time` | Time period begin (Strict ISO 8601: `YYYY-MM-DDThh:mm:ssZ`). | `acdd:time_coverage_start` | **ARCHIVAL MANDATORY** | 
| `end_time` | Time period end (Strict ISO 8601: `YYYY-MM-DDThh:mm:ssZ`). | `acdd:time_coverage_end` | **ARCHIVAL MANDATORY** | 
| `geometry` | Well-Known Text (WKT) representing the footprint. | `locn:geometry` | **ARCHIVAL MANDATORY** | 

### 2.2 Platforms.csv (The Vehicles / SensorThings "Things")

*Tracks the physical vehicles (Ships, AUVs, UAVs). Platforms are tied to the specific event tier they operate within (e.g., a Ship to a Cruise, an AUV to a Deployment event).*

| CSV Header | Description | Ontology Mapping | Requirement Level | 
| ----- | ----- | ----- | ----- |
| `event_id` | **FOREIGN KEY:** Links back to the relevant Event. | `dcterms:isPartOf` | **SYSTEM MANDATORY** | 
| `platform_id` | **PRIMARY KEY:** UUID or Machine key for the specific vehicle. | `dc:identifier` | **SYSTEM MANDATORY** | 
| `platform_name` | Human-readable local name (e.g., "R/V Atlantis"). | `dc:title` | **ARCHIVAL MANDATORY** | 
| `platform_type` | Make/Model/Class of the vehicle (if applicable). | `acdd:platform` | RECOMMENDED | 
| `platform_vocabulary` | Vocabulary used for categorization (e.g., GCMD Platform Keywords). | `acdd:platform_vocabulary` | RECOMMENDED | 

### 2.3 Sensors.csv (The Instruments)

*Tracks the specific measurement devices. Sensors are tied directly to the event in which they are taking readings. We enforce "one platform per event", avoiding complex Sensor-to-Platform foreign keys.*

| CSV Header | Description | Ontology Mapping | Requirement Level | 
| ----- | ----- | ----- | ----- |
| `event_id` | **FOREIGN KEY:** Links back to the relevant Event. | `dcterms:isPartOf` | **SYSTEM MANDATORY** | 
| `sensor_id` | **PRIMARY KEY:** UUID or Machine key for the specific piece of gear. | `dc:identifier` | **SYSTEM MANDATORY** | 
| `sensor_name` | Human-readable local name (e.g., "spherecam 3"). | `dc:title` | **ARCHIVAL MANDATORY** | 
| `instrument_type` | Make/Model/Type of the sensor (e.g., "Sea-Bird SBE 911plus"). | `acdd:instrument` | RECOMMENDED | 
| `instrument_vocabulary`| Vocabulary used for categorization (e.g., GCMD Instrument Keywords).| `acdd:instrument_vocabulary` | RECOMMENDED | 

### 2.4 Variables.csv (The Measurements / SensorThings "ObservedProperty")

*Tracks the specific scientific measurements contained in the data. Usually tied to the lowest-level event (the Dataset/Drop).*

| CSV Header | Description | Ontology Mapping | Requirement Level | 
| ----- | ----- | ----- | ----- |
| `event_id` | **FOREIGN KEY:** Links back to `Events.csv`. | `dcterms:isPartOf` | **SYSTEM MANDATORY** | 
| `variable_name` | Parameter measured (e.g., "sea_water_temperature"). | `cf:standard_name` | **ARCHIVAL MANDATORY** | 
| `data_type` | Data type format (e.g., "Float32", "Video", "Image"). | `dc:type` | RECOMMENDED | 

### 2.5 Keywords.csv (The Vocabulary)

*Handles all thematic, spatial, and organizational keywords. Usually tied to the "Heavy Parent" Cruise or Survey level.*

| CSV Header | Description | Ontology Mapping | Requirement Level | 
| ----- | ----- | ----- | ----- |
| `event_id` | **FOREIGN KEY:** Links back to `Events.csv`. | `dcterms:isPartOf` | **SYSTEM MANDATORY** | 
| `vocabulary` | The thesaurus used (e.g., "GCMD Science Keywords"). | `acdd:keyword_vocabulary` | **ARCHIVAL MANDATORY** | 
| `keyword` | The exact hierarchical keyword string. | `dc:subject` | **ARCHIVAL MANDATORY** | 

### 2.6 Related_Entities.csv (The Network)

*For linking external context: funding projects, published papers, or overarching Data Access endpoints.*

| CSV Header | Description | Ontology Mapping | Requirement Level | 
| ----- | ----- | ----- | ----- |
| `event_id` | **FOREIGN KEY:** Links back to `Events.csv`. | `dcterms:isPartOf` | **SYSTEM MANDATORY** | 
| `relation_type` | Defines the linkage type (e.g., `project`, `isRelatedTo`, `download`). | `dc:relation_type` | **ARCHIVAL MANDATORY** | 
| `entity_title` | Title of the project, dataset, or paper. | `dc:title` | RECOMMENDED | 
| `entity_id` | External machine key: DOI, Accession Number, Grant ID, etc. | `dc:identifier` | RECOMMENDED | 
| `entity_url` | Direct URL / web link to the entity (e.g., STAC endpoint). | `dc:source` | **CONDITIONAL** (Req. for Data) | 

