import xml.etree.ElementTree as ET
import zipfile

def get_form_name(html_string):
    """
    Parses an HTML string to extract the content of the <h1> tag.
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
    Parses an HTML string to extract data from tables.
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
    Parses a KMZ file and groups placemarks by the form name found in their description.
    """
    with zipfile.ZipFile(kmz_file_path, 'r') as kmz:
        kml_file = next((name for name in kmz.namelist() if name.endswith('.kml')), None)
        if not kml_file:
            raise ValueError(f"No .kml file found in {kmz_file_path}")
        kml_content = kmz.read(kml_file)

    root = ET.fromstring(kml_content)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    placemarks = root.findall('.//kml:Placemark', ns)
    
    forms = {}
    for pm in placemarks:
        desc_html = pm.find('kml:description', ns).text.strip() if pm.find('kml:description', ns) is not None and pm.find('kml:description', ns).text else ''
        form_name = get_form_name(desc_html)
        if form_name:
            if form_name not in forms:
                forms[form_name] = []
            forms[form_name].append(pm)
    return forms

def extract_placemark_data(placemark):
    """
    Extracts all relevant data from a single placemark element.
    """
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
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
    
    return placemark_data
