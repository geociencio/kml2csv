# -*- coding: utf-8 -*-
"""kml_to_csv.py
Converts KML files to CSV format, extracting placemark data and grouping by form.
This script reads a KML file, extracts placemark data, groups them by form based on
the HTML description, and writes the data to a CSV file.
It allows the user to select a form and outputs the corresponding placemark data.
Usage:
    python kml_to_csv.py

Dependencies:
    - kml_parser.py: Contains functions for parsing KML and KMZ files.
    - xml.etree.ElementTree: For XML parsing.
    - zipfile: For handling KMZ files.
    - csv: For writing CSV files.
    - os: For file path operations.
    - typing: For type hinting.

    begin          : 2025-Aug-17
    git sha1       : 1234567890abcdef1234567890abcdef12345678
    copyright       : (c) 2025 by Juan M. Bernales
    email          : juanbernales at gmail dot com
    license       : GPLv3
    version        : 1.0.0
"""
import csv
from pathlib import Path
from kml_parser import (
    group_placemarks_by_form as gpbf,
    extract_placemark_data,
    parse_html_description
)

def main() -> None:
    """
    Main function to run the KML to CSV conversion process.
    """
    try:
        script_dir: Path = Path(__file__).resolve().parent
        kmz_filename: str = (
            'geopaparazzi_20250721_014514_kmz_20250817_012241.kmz'
        )
        kmz_filepath: Path = script_dir / kmz_filename
        
        if not kmz_filepath.exists():
            print(f"Input file not found: {kmz_filepath}")
            return

        forms: dict[str, list[ET.Element]] = gpbf(kmz_filepath)
        form_names: list[str] = sorted(list(forms.keys()))

        if not form_names:
            print("No forms (h1 tags in description) found.")
            return

        print("\nPlease choose a form to process:")
        for i, name in enumerate(form_names):
            print(f"{i + 1}: {name}")

        try:
            choice_ind: int = int(input("\nEnter the number of the form: ")) - 1
            if not 0 <= choice_ind < len(form_names):
                print("Invalid choice.")
                return
            selected_form_name: str = form_names[choice_ind]
        except (ValueError, IndexError):
            print("Invalid input.")
            return

        selected_placemarks: list[ET.Element] = forms[selected_form_name]

        # Determine field order from the first placemark
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        first_pm_desc_elem: ET.Element | None = selected_placemarks[0].find(
                'kml:description', ns
            )
        if first_pm_desc_elem is not None and \
           first_pm_desc_elem.text:
            first_placemark_desc_html: str = \
                first_pm_desc_elem.text.strip()
        else:
            first_placemark_desc_html: str = ''
        description_keys: list[str] = list(
            parse_html_description(first_placemark_desc_html).keys()
        )
        
        fieldnames: list[str] = ['Name', 'Longitude', 'Latitude', 'Altitude'] + \
                     description_keys


        all_placemarks_data: list[dict[str, str]] = []
        for pm in selected_placemarks:
            all_placemarks_data.append(extract_placemark_data(pm))
        
        # Define output csv path based on form name
        csv_filename: str = (
            f"{selected_form_name.replace(' ', '_').lower()}.csv"
        )
        csv_filepath: Path = script_dir / csv_filename

        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer: csv.DictWriter = csv.DictWriter(csvfile, 
                                                    fieldnames=fieldnames,
                                                    extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_placemarks_data)

        print(
            f"\nConversion successful. {len(all_placemarks_data)} placemarks "
            f"from form '{selected_form_name}' written to {csv_filepath}"
        )

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
