import xml.etree.ElementTree as ET
import zipfile

def get_form_name(html_string):
    """
    Parses an HTML string to extract the content of the <h1> tag.
    Extracts and returns the text content of the first <h1> tag 
    found in the given HTML string.

    Args:
        html_string (str): The HTML string to parse.

    Returns:
        str or None: The stripped text content of the <h1> tag if found, 
                     otherwise None.
    """
    if not html_string:
        return None
    try:
        root = ET.fromstring(f'<div>{html_string}</div>')
        h1 = root.find('.//h1')
        if h1 is not None and h1.text:
            return h1.text.strip()
    except ET.ParseError:
        return None
    return None

def parse_html_description(html_string):
    """
    Parses an HTML string containing tables and 
        extracts key-value pairs from table rows.
    Each table row is expected to have two cells: 
        the first cell is used as the key and the second as the value.
    Returns a dictionary mapping keys to values extracted from the tables.
    Args:
        html_string (str): The HTML string to parse.
    Returns:
        dict: A dictionary containing key-value pairs extracted from the HTML tables.
    example:
        input: 
        "<table>
                <tr><td>Key1</td><td>Value1</td></tr>
                <tr><td>Key2</td><td>Value2</td></tr>
        </table>"
        output: {'Key1': 'Value1', 'Key2': 'Value2'}


    """
    data = {}
    if not html_string:
        return data

    try:
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

def group_placemarks_by_form(kmz_file_path):
    """
    Parses a KMZ file and groups KML placemarks by the form name 
    extracted from their description.
    Args:
        kmz_file_path (str): Path to the KMZ file to be parsed.
    Returns:
        dict: A dictionary where keys are form names (str) and values are 
            lists of placemark elements (xml.etree.ElementTree.Element).
    Raises:
        ValueError: If no .kml file is found inside the KMZ archive.
    Note:
        The function expects a helper function `get_form_name` 
        to extract the form name from the placemark's description HTML.
    """
    with zipfile.ZipFile(kmz_file_path, 'r') as kmz:
        kml_file = None
        for name in kmz.namelist():
            if name.endswith('.kml'):
                kml_file = name
                break
        if not kml_file:
            raise ValueError(f"No .kml file found in {kmz_file_path}")
        kml_content = kmz.read(kml_file)

    root = ET.fromstring(kml_content)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    placemarks = root.findall('.//kml:Placemark', ns)
    
    forms = {}
    for pm in placemarks:
        description_element = pm.find('kml:description', ns)
        if description_element is not None and description_element.text:
            desc_html = description_element.text.strip()
        else:
            desc_html = ''
        
        form_name = get_form_name(desc_html)
        if form_name:
            if form_name not in forms:
                forms[form_name] = []
            forms[form_name].append(pm)
    return forms

def extract_placemark_data(placemark):
    """
    Extracts relevant data from a KML Placemark XML element.
    This function parses the provided Placemark element to extract its name, 
        coordinates (longitude, latitude, altitude),
        and description. The description is further processed to extract 
        additional structured data using the `parse_html_description` function.
    Args:
        placemark (xml.etree.ElementTree.Element): 
            The Placemark XML element to extract data from.
    Returns:
        dict: A dictionary containing extracted data fields 
                such as 'Name', 'Longitude', 'Latitude', 'Altitude',
                and any additional fields parsed from the description.
    Extracts all relevant data from a single placemark element.
    """
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    placemark_data = {}

    name_element = placemark.find('kml:name', ns)
    if name_element is not None and name_element.text:
        placemark_data['Name'] = name_element.text.strip()
    else:
        placemark_data['Name'] = ''

    coordinates_element = placemark.find('.//kml:coordinates', ns)
    if coordinates_element is not None and coordinates_element.text:
        coordinates_string = coordinates_element.text.strip()
        coords = coordinates_string.split(',')
        placemark_data['Longitude'] = coords[0] if len(coords) > 0 else ''
        placemark_data['Latitude'] = coords[1] if len(coords) > 1 else ''
        placemark_data['Altitude'] = coords[2] if len(coords) > 2 else ''
    else:
        placemark_data['Longitude'] = ''
        placemark_data['Latitude'] = ''
        placemark_data['Altitude'] = ''

    description_element = placemark.find('kml:description', ns)
    if description_element is not None and description_element.text:
        description_html = description_element.text.strip()
    else:
        description_html = ''
    
    description_data = parse_html_description(description_html)
    placemark_data.update(description_data)
    
    return placemark_data
