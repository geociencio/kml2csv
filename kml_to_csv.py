import os
import zipfile
import xml.etree.ElementTree as ET
import csv

def kml_to_csv(kmz_file_path, output_csv_path):
    """
    Extracts data from a KMZ file, parses the KML content, and writes it to a CSV file.

    Args:
        kmz_file_path (str): The path to the input KMZ file.
        output_csv_path (str): The path to the output CSV file.
    """
    try:
        # Find KML file inside the KMZ archive
        with zipfile.ZipFile(kmz_file_path, 'r') as kmz:
            kml_file = None
            for name in kmz.namelist():
                if name.endswith('.kml'):
                    kml_file = name
                    break

            if not kml_file:
                print(f"No .kml file found in {kmz_file_path}")
                return

            # Read KML content
            kml_content = kmz.read(kml_file)

        # Parse KML content
        root = ET.fromstring(kml_content)

        # KML namespace
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}

        # Open CSV file for writing
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write header
            csv_writer.writerow(['Name', 'Description', 'Coordinates'])

            # Find and process Placemarks
            for placemark in root.findall('.//kml:Placemark', ns):
                name_element = placemark.find('kml:name', ns)
                name = name_element.text.strip() if name_element is not None and name_element.text else ''

                description_element = placemark.find('kml:description', ns)
                description = description_element.text.strip() if description_element is not None and description_element.text else ''

                coordinates_element = placemark.find('.//kml:coordinates', ns)
                coordinates = coordinates_element.text.strip() if coordinates_element is not None and coordinates_element.text else ''

                csv_writer.writerow([name, description, coordinates])

        print(f"Conversion successful. Data written to {output_csv_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Input KMZ file (assuming it's in the same directory as the script)
    kmz_filename = 'geopaparazzi_20250721_014514_kmz_20250817_012241.kmz'
    kmz_filepath = os.path.join(script_dir, kmz_filename)

    # Output CSV file
    csv_filename = 'output.csv'
    csv_filepath = os.path.join(script_dir, csv_filename)

    if os.path.exists(kmz_filepath):
        kml_to_csv(kmz_filepath, csv_filepath)
    else:
        print(f"Input file not found: {kmz_filepath}")
