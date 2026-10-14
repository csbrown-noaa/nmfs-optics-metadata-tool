import csv
import uuid
import datetime
import os
import argparse
import xml.etree.ElementTree as ET
from jinja2 import Environment, PackageLoader

# Setup Jinja2 Environment to load templates from the package structure
# NOTE: Replace 'my_package' with the actual name of your inner python module folder.
env = Environment(loader=PackageLoader('my_package', 'templates'))
survey_template = env.get_template('survey_template.xml')
cruise_template = env.get_template('cruise_template.xml')
site_template = env.get_template('site_template.xml')

# ISO XML Namespaces needed for parsing child records
NAMESPACES = {
    'gmi': 'http://www.isotc211.org/2005/gmi',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gml': 'http://www.opengis.net/gml/3.2'
}

# ==========================================
# BUSINESS LOGIC: XML GENERATION & PARSING
# ==========================================

def _calculate_convex_hull(points: list) -> list:
    """
    Pure Python implementation of Andrew's Monotone Chain Convex Hull algorithm.
    Takes a list of (lon, lat) tuples and returns the hull boundary points.
    """
    points = sorted(set(points))
    
    if len(points) <= 1:
        return points

    # Cross product of vectors (O->A) and (O->B)
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    # Build lower hull
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Concatenation of lower and upper hull closes the polygon automatically
    return lower[:-1] + upper

def _extract_unified_extents(xml_strings: list) -> dict:
    """
    Universal extractor: Parses any mix of ISO XML records (Sites, Transects, Cruises)
    to calculate the bounding box, a precise Convex Hull polygon, and time span.
    """
    all_lats, all_lons, all_times = [], [], []
    
    for xml_str in xml_strings:
        root = ET.fromstring(xml_str)
        
        # 1. Extract Time
        begin = root.find('.//gml:beginPosition', NAMESPACES)
        end = root.find('.//gml:endPosition', NAMESPACES)
        if begin is not None and begin.text: all_times.append(begin.text)
        if end is not None and end.text: all_times.append(end.text)
        
        # 2. Extract Point Geometry (Sites)
        for p in root.findall('.//gml:pos', NAMESPACES):
            coords = p.text.split()
            all_lats.append(float(coords[0]))
            all_lons.append(float(coords[1]))
            
        # 3. Extract Line/Polygon Geometry (Transects or lower-level hulls)
        for l in root.findall('.//gml:posList', NAMESPACES):
            coords = l.text.split()
            all_lats.extend([float(coords[i]) for i in range(0, len(coords), 2)])
            all_lons.extend([float(coords[i]) for i in range(1, len(coords), 2)])
            
        # 4. Extract Bounding Box Geometry (If extracting from intermediate Cruises)
        west = root.find('.//gmd:westBoundLongitude/gco:Decimal', NAMESPACES)
        east = root.find('.//gmd:eastBoundLongitude/gco:Decimal', NAMESPACES)
        south = root.find('.//gmd:southBoundLatitude/gco:Decimal', NAMESPACES)
        north = root.find('.//gmd:northBoundLatitude/gco:Decimal', NAMESPACES)
        
        if all(x is not None and x.text for x in [west, east, south, north]):
            w, e, s, n = float(west.text), float(east.text), float(south.text), float(north.text)
            # Add all four corners to our point pool
            all_lons.extend([w, e, e, w])
            all_lats.extend([s, s, n, n])

    all_times.sort()
    
    # Create the Convex Hull
    points = list(zip(all_lons, all_lats))
    hull_points = _calculate_convex_hull(points)
    
    # ISO 19115/GML requires polygons to have area (min 3 distinct points + 1 closing point = 4)
    if len(hull_points) < 4:
        # Fallback to a minimal buffer around whatever points we have to form a valid box
        min_lon = min(all_lons) if all_lons else 0.0
        max_lon = max(all_lons) if all_lons else 0.0
        min_lat = min(all_lats) if all_lats else 0.0
        max_lat = max(all_lats) if all_lats else 0.0
        
        # Expand infinitesimally if it's a perfectly flat line or single point
        if min_lon == max_lon: min_lon -= 0.001; max_lon += 0.001
        if min_lat == max_lat: min_lat -= 0.001; max_lat += 0.001
            
        hull_points = [(min_lon, min_lat), (max_lon, min_lat), (max_lon, max_lat), (min_lon, max_lat), (min_lon, min_lat)]

    # Format the polygon posList string as "lat lon lat lon..."
    polygon_str = " ".join(f"{lat} {lon}" for lon, lat in hull_points)

    return {
        'south': min(all_lats) if all_lats else 0.0,
        'north': max(all_lats) if all_lats else 0.0,
        'west': min(all_lons) if all_lons else 0.0,
        'east': max(all_lons) if all_lons else 0.0,
        'polygon_pos_list': polygon_str,
        'start_time': all_times[0] if all_times else '',
        'end_time': all_times[-1] if all_times else ''
    }

def create_site_xml(site_metadata: dict) -> str:
    """
    Takes site-level variables and outputs a rendered XML string.
    Expects cruise_uuid to be injected into site_metadata before calling.
    """
    site_metadata['site_uuid'] = str(uuid.uuid4())
    site_metadata['today_date'] = datetime.date.today().isoformat()
    return site_template.render(**site_metadata)


def create_cruise_xml(cruise_metadata: dict, site_xml_strings: list) -> str:
    """
    Takes cruise-level variables and a list of child Site XML strings.
    Extracts the unified bounding geometry from the children and outputs the Cruise XML.
    """
    extents = _extract_unified_extents(site_xml_strings)
    
    # Merge extracted extents and current date into cruise metadata
    template_data = {
        **cruise_metadata,
        'cruise_south': extents['south'],
        'cruise_north': extents['north'],
        'cruise_west': extents['west'],
        'cruise_east': extents['east'],
        'cruise_polygon_pos_list': extents['polygon_pos_list'],
        'cruise_start_time': extents['start_time'],
        'cruise_end_time': extents['end_time'],
        'today_date': datetime.date.today().isoformat()
    }
    
    return cruise_template.render(**template_data)


def create_survey_xml(survey_metadata: dict, cruise_xml_strings: list) -> str:
    """
    Takes survey-level variables and a list of child Cruise XML strings.
    Extracts the unified bounding geometry from the cruises and outputs the Survey XML.
    """
    extents = _extract_unified_extents(cruise_xml_strings)
    
    template_data = {
        **survey_metadata,
        'survey_south': extents['south'],
        'survey_north': extents['north'],
        'survey_west': extents['west'],
        'survey_east': extents['east'],
        'survey_polygon_pos_list': extents['polygon_pos_list'],
        'survey_start_time': extents['start_time'],
        'survey_end_time': extents['end_time'],
        'today_date': datetime.date.today().isoformat()
    }
    
    return survey_template.render(**template_data)


# ==========================================
# FILE ORCHESTRATION: I/O AND DATA PASSING
# ==========================================

def process_cruise_batch(csv_filepath: str, output_dir: str, cruise_metadata: dict):
    """
    Reads a CSV of site data, creates Site XMLs, writes them to disk,
    and then generates and writes the parent Cruise XML.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    site_xml_strings = []
    
    with open(csv_filepath, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Merge the CSV row data with the overarching cruise data (UUIDs, ship name, etc.)
            site_data = {**row, **cruise_metadata}
            
            # 1. Generate Site XML String
            site_xml = create_site_xml(site_data)
            site_xml_strings.append(site_xml)
            
            # 2. Write Site XML to disk
            safe_name = row['site_name'].replace(' ', '_').replace('/', '_')
            site_filename = f"site_{safe_name}.xml"
            site_filepath = os.path.join(output_dir, site_filename)
            
            with open(site_filepath, 'w') as out_f:
                out_f.write(site_xml)
            print(f"  -> Saved {site_filename}")

    # 3. Generate Cruise XML String (passing the site XMLs for rollup)
    cruise_xml = create_cruise_xml(cruise_metadata, site_xml_strings)
    
    # 4. Write Cruise XML to disk
    safe_cruise_name = cruise_metadata['cruise_name'].replace(' ', '_')
    cruise_filename = f"cruise_{safe_cruise_name}.xml"
    cruise_filepath = os.path.join(output_dir, cruise_filename)
    
    with open(cruise_filepath, 'w') as out_f:
        out_f.write(cruise_xml)
    print(f"\nSuccess! Saved Parent Record: {cruise_filename}")
    
    return cruise_filepath


def process_survey_batch(survey_metadata: dict, cruise_xml_filepaths: list, output_filepath: str):
    """
    Reads a list of existing Cruise XML files from disk, generates the
    grandparent Survey XML, and writes it to disk.
    """
    cruise_xml_strings = []
    
    # 1. Read Cruise XMLs into memory
    for path in cruise_xml_filepaths:
        with open(path, 'r') as f:
            cruise_xml_strings.append(f.read())
            
    # 2. Generate Survey XML String
    survey_xml = create_survey_xml(survey_metadata, cruise_xml_strings)
    
    # 3. Write Survey XML to disk
    with open(output_filepath, 'w') as f:
        f.write(survey_xml)
    print(f"Success! Saved Project Record: {output_filepath}")
    
    return output_filepath


# ==========================================
# COMMAND LINE INTERFACE
# ==========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ISO 19115-2 XML metadata for a Cruise Batch.")
    
    # File I/O arguments
    parser.add_argument('--csv', required=True, help='Path to the input cruise CSV data file')
    parser.add_argument('--outdir', default='.', help='Output directory for the generated XML files')
    
    # Cruise-level metadata arguments
    parser.add_argument('--survey-uuid', required=True, help='UUID of the overarching Survey (Grandparent)')
    parser.add_argument('--cruise-name', required=True, help='Name of the Cruise (e.g., Pac-Geo-01)')
    parser.add_argument('--ship-name', required=True, help='Name of the Vessel (e.g., R/V Atlantis)')
    
    args = parser.parse_args()
    
    # Construct the metadata payload to pass into our business logic
    cruise_metadata_payload = {
        'survey_uuid': args.survey_uuid,
        'cruise_uuid': str(uuid.uuid4()), # Generate a fresh UUID for this new cruise
        'cruise_name': args.cruise_name,
        'ship_name': args.ship_name
    }
    
    print(f"Starting batch process for cruise '{args.cruise_name}'...")
    process_cruise_batch(
        csv_filepath=args.csv, 
        output_dir=args.outdir, 
        cruise_metadata=cruise_metadata_payload
    )
