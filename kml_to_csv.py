import os
import zipfile
import xml.etree.ElementTree as ET
import csv

def parse_html_description(html_string):
    """
    Parses an HTML string to extract data from tables.

    Args:
        html_string (str): The HTML content from the description tag.

    Returns:
        dict: A dictionary with the extracted data, preserving insertion order.
    """
    data = {}
    if not html_string:
        return data

    try:
        # Wrap the HTML fragment to make it a valid XML for parsing
        root = ET.fromstring(f'<div>{html_string}</div>')
        tables = root.findall('.//table')
        for table in tables:
            rows = table.findall('.//tr')
            for row in rows:
                cells = row.findall('.//td')
                if len(cells) == 2:
                    key = cells[0].text.strip() if cells[0].text else ''
                    value = cells[1].text.strip() if cells[1].text else ''
                    if key:
                        data[key] = value
    except ET.ParseError:
        pass
    return data

def kml_to_csv_interactive_multiple(kmz_file_path, output_csv_path):
    """
    Extracts data from a KMZ file, prompts the user to select a placemark name,
    parses all placemarks with that name, and writes them to a CSV file,
    preserving the original order of fields.
    """
    try:
        with zipfile.ZipFile(kmz_file_path, 'r') as kmz:
            kml_file = next((name for name in kmz.namelist() if name.endswith('.kml')), None)
            if not kml_file:
                print(f"No .kml file found in {kmz_file_path}")
                return
            kml_content = kmz.read(kml_file)

        root = ET.fromstring(kml_content)
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}

        placemarks = root.findall('.//kml:Placemark', ns)
        
        placemark_names = sorted(list(set([pm.find('kml:name', ns).text for pm in placemarks if pm.find('kml:name', ns) is not None and pm.find('kml:name', ns).text])))

        if not placemark_names:
            print("No placemarks with names found.")
            return

        print("\nPlease choose a placemark name to process:")
        for i, name in enumerate(placemark_names):
            print(f"{i + 1}: {name}")

        try:
            choice_index = int(input("\nEnter the number of the placemark name: ")) - 1
            if not 0 <= choice_index < len(placemark_names):
                print("Invalid choice.")
                return
            selected_name = placemark_names[choice_index]
        except (ValueError, IndexError):
            print("Invalid input.")
            return

        selected_placemarks = [pm for pm in placemarks if pm.find('kml:name', ns) is not None and pm.find('kml:name', ns).text == selected_name]

        if not selected_placemarks:
            print(f"No placemarks found with the name '{selected_name}'.")
            return

        # Determine field order from the first selected placemark
        first_placemark_desc_html = selected_placemarks[0].find('kml:description', ns).text.strip() if selected_placemarks[0].find('kml:description', ns) is not None else ''
        description_keys = list(parse_html_description(first_placemark_desc_html).keys())
        
        fieldnames = ['Name', 'Longitude', 'Latitude', 'Altitude'] + description_keys

        all_placemarks_data = []
        for placemark in selected_placemarks:
            placemark_data = {}
            
            name_element = placemark.find('kml:name', ns)
            placemark_data['Name'] = name_element.text.strip() if name_element is not None and name_element.text else ''

            coordinates_element = placemark.find('.//kml:coordinates', ns)
            coordinates_string = coordinates_element.text.strip() if coordinates_element is not None and coordinates_element.text else ''
            if coordinates_string:
                coords = coordinates_string.split(',')
                placemark_data['Longitude'] = coords[0] if len(coords) > 0 else ''
                placemark_data['Latitude'] = coords[1] if len(coords) > 1 else ''
                placemark_data['Altitude'] = coords[2] if len(coords) > 2 else ''
            else:
                placemark_data['Longitude'] = ''
                placemark_data['Latitude'] = ''
                placemark_data['Altitude'] = ''

            description_element = placemark.find('kml:description', ns)
            description_html = description_element.text.strip() if description_element is not None and description_element.text else ''
            
            description_data = parse_html_description(description_html)
            placemark_data.update(description_data)
            
            all_placemarks_data.append(placemark_data)

        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_placemarks_data)

        print(f"\nConversion successful. {len(all_placemarks_data)} placemarks with the name '{selected_name}' written to {output_csv_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    kmz_filename = 'geopaparazzi_20250721_014514_kmz_20250817_012241.kmz'
    kmz_filepath = os.path.join(script_dir, kmz_filename)
    csv_filename = 'output.csv'
    csv_filepath = os.path.join(script_dir, csv_filename)

    if os.path.exists(kmz_filepath):
        kml_to_csv_interactive_multiple(kmz_filepath, csv_filepath)
    else:
        print(f"Input file not found: {kmz_filepath}")
