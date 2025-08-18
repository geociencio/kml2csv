# -- coding: utf-8 -*-
"""kml_parser.py
Contains functions for parsing KML and KMZ files, extracting placemark data,
and grouping them by form based on the HTML description.
This module provides utilities to read KML files, extract relevant data from 
placemarks, group them by form, and parse HTML descriptions to extract 
additional structured data.
Usage:
    from kml_parser import (
        group_placemarks_by_form,
        extract_placemark_data,
        parse_html_description
    )
Dependencies:
    - xml.etree.ElementTree: For XML parsing.
    - zipfile: For handling KMZ files.
    - html.parser: For parsing HTML content.
    - typing: For type hinting.
Example:
    from kml_parser import group_placemarks_by_form, extract_placemark_data 
    kmz_file_path = 'path/to/your/file.kmz'
    forms = group_placemarks_by_form(kmz_file_path)
    for form_name, placemarks in forms.items():
        print(f"Form: {form_name}")
        for placemark in placemarks:
            data = extract_placemark_data(placemark)
            print(data)
    This module is designed to be used as a library for KML/KMZ file processing
    and can be integrated into larger applications or scripts.  
    begin          : 2025-Aug-17
    git sha1       : 1234567890abcdef1234567890abcdef12345678
    copyright       : (c) 2025 by Juan M. Bernales
    email          : juanbernales at gmail dot com
    license       : GPLv3
    version        : 1.0.0
"""
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class PlacemarkData:
    """Data class to hold extracted placemark data.
    This class is used to store the name, coordinates (longitude, latitude, altitude),
    and any additional structured data extracted from the placemark's description.
    """
    name: str = ''
    longitude: str = ''
    latitude: str = ''
    altitude: str = ''
    extra: dict[str, Any] = field(default_factory=dict)


NO_FORM = "__NO_FORM__"
                        # This constant is used to represent placemarks that do 
                        # not belong to any specific form. It is used as a
                        # default value when no form name can be extracted from 
                        # the placemark's description.
KML_NS = {'kml': 'http://www.opengis.net/kml/2.2'}
                        # This namespace dictionary is used to define the KML 
                        # namespace for XML parsing. It allows the ElementTree 
                        # module to correctly interpret KML elements when 
                        # searching for them in the XML tree.

class TableHTMLParser(HTMLParser):
    """
    A simple HTML parser to extract table data.
    This class extends the HTMLParser from the html.parser module 
    to specifically parse HTML tables and extract key-value pairs 
    from table rows.
    """
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.current_row = []  # type: list[str]
        self.data = {}  # type: dict[str, str]

    def handle_starttag(self, tag, attrs):
        """Handles the start of an HTML tag."""
        if tag.lower() == 'td':
            self.in_td = True

    def handle_endtag(self, tag):
        """Handles the end of an HTML tag."""
        if tag.lower() == 'td':
            self.in_td = False
        elif tag.lower() == 'tr':
            if len(self.current_row) == 2:
                key = self.current_row[0].strip()
                value = self.current_row[1].strip()
                if key:
                    self.data[key] = value
            self.current_row = []

    def handle_data(self, data):
        """Handles the data within an HTML tag."""
        if self.in_td:
            self.current_row.append(data)

class H1HTMLParser(HTMLParser):
    """
    A simple HTML parser to extract the content of the <h1> tag.
    This class extends the HTMLParser from the html.parser module
    to specifically parse HTML and extract the text content of the first <h1> 
    tag found.
    """
    def __init__(self):
        super().__init__()
        self.in_h1 = False
        self.text = None
    def handle_starttag(self, tag, attrs):
        """Handles the start of an HTML tag."""
        if tag.lower() == 'h1':
            self.in_h1 = True

    def handle_endtag(self, tag):
        """Handles the end of an HTML tag."""
        if tag.lower() == 'h1':
            self.in_h1 = False

    def handle_data(self, data):
        """Handles the data within an HTML tag."""
        if self.in_h1 and not self.text:
            self.text =data.strip()

def get_form_name(html_string: str) -> Optional[str]:
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
    # if not html_string:
    #     return None
    # try:
    #     root = ET.fromstring(f'<div>{html_string}</div>')
    #     h1 = root.find('.//h1')
    #     if h1 is not None and h1.text:
    #         return h1.text.strip()
    # except ET.ParseError:
    #     return None
    # return None
    parser = H1HTMLParser()
    parser.feed(html_string or "")
    return parser.text

def parse_html_description(html_string: str) -> Dict[str, str]:
    """
    Parses an HTML string containing tables and 
        extracts key-value pairs from table rows.
    Each table row is expected to have two cells: 
        the first cell is used as the key and the second as the value.
    Returns a dictionary mapping keys to values extracted from the tables.
    Args:
        html_string (str): The HTML string to parse.
    Returns:
        dict: A dictionary containing key-value pairs 
        extracted from the HTML tables.
    example:
        input: 
        "<table>
                <tr><td>Key1</td><td>Value1</td></tr>
                <tr><td>Key2</td><td>Value2</td></tr>
        </table>"
        output: {'Key1': 'Value1', 'Key2': 'Value2'}


    """
    parser = TableHTMLParser()
    parser.feed(html_string or "")
    return parser.data

def group_placemarks_by_form(kmz_file_path: str) -> dict[str, list[ET.Element]]:
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
    placemarks = root.findall('.//kml:Placemark', KML_NS)
    forms = {}
    for pm in placemarks:
        description_element = pm.find('kml:description', KML_NS)
        if description_element is not None and description_element.text:
            desc_html = description_element.text.strip()
        else:
            desc_html = '' 
        form_name = get_form_name(desc_html) or NO_FORM
        if form_name:
            if form_name not in forms:
                forms[form_name] = []
            forms[form_name].append(pm)
    return forms

def extract_placemark_data(placemark: ET.Element) -> dict[str, str]:
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
    name = ''
    longitude = ''
    latitude = ''
    altitude = ''
    extra = {}

    name_element = placemark.find('kml:name', KML_NS)
    if name_element is not None and name_element.text:
        name = name_element.text.strip()

    coordinates_element = placemark.find('.//kml:coordinates', KML_NS)
    if coordinates_element is not None and coordinates_element.text:
        coordinates_string = coordinates_element.text.strip()
        coords = coordinates_string.split(',')
        if len(coords) == 3:
            longitude = coords[0]
            latitude = coords[1]
            altitude = coords[2]
        elif len(coords) == 2:
            longitude = coords[0]
            latitude = coords[1]
        elif len(coords) == 1:
            longitude = coords[0]
    description_element = placemark.find('kml:description', KML_NS)
    if description_element is not None and description_element.text:
        description_html = description_element.text.strip()
        extra = parse_html_description(description_html)
    return PlacemarkData(name=name, longitude=longitude, latitude=latitude, altitude=altitude, extra=extra)
