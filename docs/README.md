# NMFS Optics Metadata Specification & Translation Pipeline

## 1. Introduction

Welcome to the NMFS Optics Metadata specification and toolset.
This repository provides both a standardized schema and an automated pipeline for generating standard-compliant ISO 19115-2 XML metadata for oceanographic optical surveys, cruises, and discrete sampling events.

**The Goal (The Prize):** 
Our ultimate objective is to achieve **FAIR data principles** (Findable, Accessible, Interoperable, Reusable) and meet strict NOAA/NCEI compliance.
Reaching this standard ensures our valuable scientific data is preserved in long-term archives and becomes globally discoverable across NMFS and beyond.
It is important to note that this schema is specifically designed for granular, site/transect-level metadata (the "leaf nodes" of a cruise, such as drop sites, CTD casts, and camera transects).
While there are existing enterprise tools for overarching project and large-dataset metadata (such as NOAA's InPort), capturing the highly detailed, site-by-site field operations is often where the bottleneck occurs.
Because our ultimate goal is strict ISO 19115 compliance, enterprise catalogs like InPort become a natural target; since InPort supports ISO 19115, ingesting your site-level data into it becomes a trivial "freebie" once standardization is achieved.

## 2. The Context & The Challenge

We recognize and validate that across our organization, many groups maintain highly effective, customized local databases and file schemas.
These systems have been perfected over years of operational use and represent a massive amount of hard work by dedicated field scientists, biologists, and database managers. 

However, transitioning data from these comfortable, relational formats into the highly nested, strict ISO 19115-2 XML required by federal archives is often frustrating, time-consuming, and requires specialized knowledge of XML and complex metadata ontologies.

**The "Why":** 
To reach the NCEI/FAIR data prize, our metadata must speak a universal language.
But we do not expect scientists or data maintainers to become XML experts to get there.

## 3. The Stepping Stone: The 5-Table CSV Schema

Think of this repository as the bridge.
We meet data maintainers halfway with a familiar, flat format: the CSV file. 

**A Crucial Distinction:** 
We designed this specific 5-table *layout* for ease of use, but we did not invent the *requirements*.
The schema is carefully reverse-engineered to capture all of the mandatory fields, vocabularies, and linkages strictly required by NCEI and ISO 19115.
We are simply translating their complex rules into a format that is much easier to map your existing data into.

The schema consists of 5 core conceptual components:
* **Events:** The discrete field operations (e.g., camera transects, drop sites).
* **Platforms:** The vehicles used during the operations (e.g., ships, AUVs).
* **Sensors:** The specific instruments collecting the data.
* **Variables:** The scientific parameters measured.
* **Related Entities:** Links to physical files, downloads, or external resources.

For the full, detailed specification, please see the [**schema.md**](schema.md) file in this repository.

## 4. Translation Tooling

Once your data is mapped into this 5-table CSV format, this repository provides automated Python tools to handle the heavy lifting.
The tool translates your rows of CSV data into robust, 3-tier hierarchical metadata (Survey > Cruise > Dataset) as valid ISO 19115-2 XML.

### Installation & Basic Usage

This package is configured using `flit`.
You can install it directly into your virtual environment:

```bash
cd nmfs-optics-metadata-tool
pip install .
```

You can then run the command-line interface to process a CSV file into a directory of XML records, rolling them up into a parent cruise record:

```bash
python -m nmfs_optics_metadata_tool.generate_iso \
  --csv tests/example_data.csv \
  --outdir ./xml_output \
  --survey-uuid "b2a3c4d5-6e7f-8a9b-0c1d-2e3f4a5b6c7d" \
  --cruise-name "Pac-Geo-01" \
  --ship-name "R/V Atlantis"
```

## 5. Contributing

We would love to have your contributions that improve current functionality, fix bugs, or add new features.
See [the contributing guidelines](CONTRIBUTING.md) for more info.

## 6. Disclaimer

This repository is a scientific product and is not official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce.
All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use.
Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law.
Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce.
The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.

