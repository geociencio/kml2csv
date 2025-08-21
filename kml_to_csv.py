# -*- coding: utf-8 -*-
"""kml_to_csv.py
Converts KML files to CSV format, extracting placemark data and grouping by form.
This script reads a KML file, extracts placemark data, groups them by form based on
the HTML description, and writes the data to a CSV file.
It allows the user to select a form and outputs the corresponding placemark data.
Usage:
    python kml_to_csv.py <input_file> [-o <output_directory>]

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
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from dataclasses import asdict
from kml_parser import (
    group_placemarks_by_form as gpbf,
    extract_placemark_data,
    parse_html_description
)

def main() -> None:
    """
    Main function to run the KML to CSV conversion process.
    """
    parser = argparse.ArgumentParser(
        description='Converts KML files to CSV format, extracting placemark data and grouping by form.'
    )
    parser.add_argument('input_file', help='Path to the input KML/KMZ file.')
    parser.add_argument('-o', '--output-dir', default='.', help='Output directory for the CSV file. Defaults to the current directory.')
    args = parser.parse_args()

    try:
        kmz_filepath: Path = Path(args.input_file)
        
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
        
        fieldnames: list[str] = ['name', 'longitude', 'latitude', 'altitude'] + \
                     description_keys


        all_placemarks_data: list[dict[str, str]] = []
        for pm in selected_placemarks:
            placemark_data_obj = extract_placemark_data(pm)
            # Convert PlacemarkData object to a dictionary
            placemark_dict = asdict(placemark_data_obj)
            # Flatten the 'extra' dictionary into the main dictionary
            if 'extra' in placemark_dict:
                placemark_dict.update(placemark_dict.pop('extra'))
            all_placemarks_data.append(placemark_dict)
        
        # Define output csv path based on form name
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_filename: str = (
            f"{selected_form_name.replace(' ', '_').lower()}.csv"
        )
        csv_filepath: Path = output_dir / csv_filename

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

    except FileNotFoundError as fnf_error:
        print(f"File not found: {fnf_error}")
    except ET.ParseError as parse_error:
        print(f"Error parsing KML file: {parse_error}")
    except csv.Error as csv_error:
        print(f"Error writing CSV file: {csv_error}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
