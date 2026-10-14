# ISO 19115-2 NMFS Optics Metadata Generator

This package provides a lightweight, automated pipeline for generating standard-compliant ISO 19115-2 XML metadata for oceanographic surveys, cruises, and discrete sampling events (drop sites and transects). 

## Purpose

Creating highly nested ISO XML metadata by hand is tedious and error-prone. This tool bridges the gap between field scientists (who prefer working with flat CSV files) and data repositories like NOAA/NCEI (which require strictly validated XML). 

By utilizing Jinja2 templates, this package automatically translates rows of CSV data into a robust, 3-tier hierarchical metadata structure:
1. **Survey (Project Level):** The overarching initiative (e.g., a multi-year grant).
2. **Cruise (Series Level):** An individual deployment on a specific vessel. The spatial and temporal bounds are automatically calculated by calculating the convex hull of all child sites.
3. **Site/Transect (Dataset Level):** Discrete events such as CTD casts or towed camera transects, complete with platform and instrument acquisition details.

## Package Structure

```text
nmfs-optics-metadata-tool/
├── pyproject.toml
├── README.md
├── tests/
│   └── example_data.csv        <-- Sample data for testing
└── nmfs-optics-metadata-tool/
    ├── __init__.py
    ├── generate_iso.py         <-- CLI application and business logic
    └── templates/              <-- Packaged XML Jinja2 templates
        ├── site_template.xml
        ├── cruise_template.xml
        └── survey_template.xml
```

## Installation

This package is configured using `flit`. You can install it directly into your virtual environment:

```bash
# Clone the repository and navigate into it
cd nmfs-optics-metadta-tool

# Install the package and its dependencies (like Jinja2)
pip install .
```

## How to Run the Example Data

We have included a sample dataset in the `tests/` directory to demonstrate how the pipeline works. 

The main script exposes a command-line interface. You provide the CSV file, an output directory, and the overarching metadata variables for the cruise you are processing. The script will handle the generation of child records and automatically roll them up into a parent cruise record.

Run the following command from the root of the repository:

```bash
python -m nmfs_optics_metadata_tool.generate_iso \
  --csv tests/example_data.csv \
  --outdir ./xml_output \
  --survey-uuid "b2a3c4d5-6e7f-8a9b-0c1d-2e3f4a5b6c7d" \
  --cruise-name "Pac-Geo-01" \
  --ship-name "R/V Atlantis"
```

### What to Expect

Upon running the command, the script will:
1. Read `tests/example_data.csv`.
2. Generate an individual `dataset` XML file for every row (e.g., `site_CTD_Cast_01.xml`, `site_Transect_Alpha.xml`) and save them to `./xml_output`.
3. Geometrically process all coordinates to create a high-fidelity spatial bounding polygon (Convex Hull).
4. Generate a parent `series` XML file (`cruise_Pac-Geo-01.xml`) encompassing all child dataset extents.

You can then inspect the `./xml_output` directory to view the generated, NOAA-compliant ISO 19115-2 XML records.

# Contributing

We would love to have your contributions that improve current functionality, fix bugs, or add new features.  See [the contributing guidelines](CONTRIBUTING.md) for more info.

# Disclaimer

This repository is a scientific product and is not official communication of the National Oceanic and
Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project
code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the
Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub
project will be governed by all applicable Federal law. Any reference to specific commercial products,
processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or
imply their endorsement, recommendation or favoring by the Department of Commerce. The Department
of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to
imply endorsement of any commercial product or activity by DOC or the United States Government.
