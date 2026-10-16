# Relational CSV Structure for ISO/NCEI Metadata

This schema utilizes an "Event-Driven" relational model, heavily inspired by OGC SensorThings and ISO 19115-2. Instead of a single flat file, data is distributed across six CSVs linked by a common UUID (`dc:identifier`). This allows for arbitrary field hierarchies (e.g., Survey -> Cruise -> Deployment -> Site) and enables the generation of "Heavy Parent" and "Skinny Child" XML records via an "Ancestry Walk."

To ensure interoperability, column names utilize prefixes from standard vocabularies: **dc/dcterms** (Dublin Core), **acdd** (Attribute Convention for Data Discovery), and **locn** (Location Core Vocabulary).

## 1. Events.csv (The Core Tree)

*This table establishes the hierarchy, timing, spatial footprint, and overarching project details. For "Skinny Child" sites, the heavy fields (Abstract, Purpose, POCs) can be left blank (NULL); the generation script will inherit them by walking up the `dcterms:isPartOf` chain. Rule of thumb: One platform operation = one event.*

| Column Name | Description / Standard | 
| ----- | ----- | 
| `dc:identifier` | **PRIMARY KEY (`event_id`):** Unique UUID for this specific event node. | 
| `dcterms:isPartOf` | **FOREIGN KEY (`parent_event_id`):** UUID of the parent event. Leave blank for top-level nodes. | 
| `dc:type` | Event category (e.g., `Survey`, `Cruise`, `Deployment`, `Drop Site`, `UAV Flight`). | 
| `dc:title` | Human-readable name or local code (e.g., "Pac-Geo-01" or "NCD-012"). | 
| `dcterms:abstract` | *(Heavy Field)* Plain-language executive summary. | 
| `acdd:purpose` | *(Heavy Field)* Scientific rationale or funding purpose. | 
| `acdd:creator_name` | *(Heavy Field)* Name of the primary Point of Contact (POC). | 
| `acdd:time_coverage_start` | Time period begin (Strict ISO 8601: `YYYY-MM-DDThh:mm:ssZ`). | 
| `acdd:time_coverage_end` | Time period end (Strict ISO 8601: `YYYY-MM-DDThh:mm:ssZ`). | 
| `locn:geometry` | Well-Known Text (WKT) representing the footprint (e.g., `POINT (lon lat)`, `LINESTRING(...)`, `POLYGON(...)`). | 

## 2. Platforms.csv (The Vehicles / SensorThings "Things")

*Tracks the physical vehicles (Ships, AUVs, UAVs). Platforms are tied to the specific event tier they operate within (e.g., a Ship to a Cruise, an AUV to a Deployment event).*

| Column Name | Description / Standard | 
| ----- | ----- | 
| `dc:identifier` | **FOREIGN KEY (`event_id`):** Links back to the relevant Event in `Events.csv`. | 
| `dc:identifier_platform` | **PRIMARY KEY:** UUID or Machine key for the specific vehicle. | 
| `dc:title` | Human-readable local name (e.g., "R/V Atlantis" or "UAV-Alpha"). | 
| `acdd:platform` | Make/Model/Class of the vehicle (if applicable). | 
| `acdd:platform_vocabulary` | Vocabulary used for categorization (e.g., GCMD Platform Keywords). | 

## 3. Sensors.csv (The Instruments)

*Tracks the specific measurement devices. Sensors are tied directly to the event in which they are taking readings. Because we enforce "one platform per event", we do not need complex Sensor-to-Platform foreign keys here; the Event ID handles the relationship.*

| Column Name | Description / Standard | 
| ----- | ----- | 
| `dc:identifier` | **FOREIGN KEY (`event_id`):** Links back to the relevant Event in `Events.csv`. | 
| `dc:identifier_sensor` | **PRIMARY KEY:** UUID or Machine key for the specific piece of gear. | 
| `dc:title` | Human-readable local name (e.g., "spherecam 3"). | 
| `acdd:instrument` | Make/Model/Type of the sensor (e.g., "Sea-Bird SBE 911plus"). | 
| `acdd:instrument_vocabulary` | Vocabulary used for categorization (e.g., GCMD Instrument Keywords). | 

## 4. Variables.csv (The Measurements / SensorThings "ObservedProperty")

*Tracks the specific scientific measurements contained in the data. Usually tied to the lowest-level event (the Dataset/Drop).*

| Column Name | Description / Standard | 
| ----- | ----- | 
| `dc:identifier` | **FOREIGN KEY (`event_id`):** Links back to `Events.csv`. | 
| `cf:standard_name` | Parameter measured (e.g., "sea_water_temperature", "acoustic_backscatter"). | 
| `dc:type` | Data type format (e.g., "Float32", "Video", "Image"). | 

## 5. Keywords.csv (The Vocabulary)

*Handles all thematic, spatial, and organizational keywords. Usually tied to the "Heavy Parent" Cruise or Survey level.*

| Column Name | Description / Standard | 
| ----- | ----- | 
| `dc:identifier` | **FOREIGN KEY (`event_id`):** Links back to `Events.csv`. | 
| `acdd:keyword_vocabulary` | The thesaurus used (e.g., "GCMD Science Keywords", "GCMD Location"). | 
| `dc:subject` | The exact hierarchical keyword string (e.g., "Oceans > Ocean Temperature > Water Temperature"). | 

## 6. Related_Entities.csv (The Network)

*For linking external context: funding projects, overarching initiatives, published papers, or actual data download links.*

| Column Name | Description / Standard | 
| ----- | ----- | 
| `dc:identifier` | **FOREIGN KEY (`event_id`):** Links back to `Events.csv`. | 
| `dc:relation_type` | Defines the linkage type (e.g., `project`, `isRelatedTo`, `isReferencedBy`, `download`). | 
| `dc:title` | Title of the project, dataset, or paper. | 
| `dc:identifier_related` | External machine key: DOI, Accession Number, Grant ID, etc. | 
| `dc:source` | Direct URL / web link to the entity (if applicable). | 

