import os
import csv
from kml_parser import group_placemarks_by_form, extract_placemark_data, parse_html_description

def main():
    """
    Main function to run the KML to CSV conversion process.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        kmz_filename = 'geopaparazzi_20250721_014514_kmz_20250817_012241.kmz'
        kmz_filepath = os.path.join(script_dir, kmz_filename)
        
        if not os.path.exists(kmz_filepath):
            print(f"Input file not found: {kmz_filepath}")
            return

        forms = group_placemarks_by_form(kmz_filepath)
        form_names = sorted(list(forms.keys()))

        if not form_names:
            print("No forms (h1 tags in description) found.")
            return

        print("\nPlease choose a form to process:")
        for i, name in enumerate(form_names):
            print(f"{i + 1}: {name}")

        try:
            choice_index = int(input("\nEnter the number of the form: ")) - 1
            if not 0 <= choice_index < len(form_names):
                print("Invalid choice.")
                return
            selected_form_name = form_names[choice_index]
        except (ValueError, IndexError):
            print("Invalid input.")
            return

        selected_placemarks = forms[selected_form_name]

        # Determine field order from the first placemark
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        first_placemark_desc_html = selected_placemarks[0].find('kml:description', ns).text.strip() if selected_placemarks[0].find('kml:description', ns) is not None else ''
        description_keys = list(parse_html_description(first_placemark_desc_html).keys())
        
        fieldnames = ['Name', 'Longitude', 'Latitude', 'Altitude'] + description_keys


        all_placemarks_data = []
        for pm in selected_placemarks:
            all_placemarks_data.append(extract_placemark_data(pm))
        
        # Define output csv path based on form name
        csv_filename = f"{selected_form_name.replace(' ', '_').lower()}.csv"
        csv_filepath = os.path.join(script_dir, csv_filename)

        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_placemarks_data)

        print(f"\nConversion successful. {len(all_placemarks_data)} placemarks from form '{selected_form_name}' written to {csv_filepath}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
