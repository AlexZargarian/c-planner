import requests
from bs4 import BeautifulSoup
import csv
import os

def scrape_aua_courses(url, output_csv_filename='aua_cluster_scraped.csv'):
    """
    aua.am-scraper.py
    Scrapes course information from the given URL and saves it to a CSV file.

    Args:
        url (str): The URL of the webpage to scrape.
        output_csv_filename (str): The name of the CSV file to save the data to.
    """
    print(f"Attempting to scrape data from: {url}")
    try:
        # Fetch the HTML content from the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        print("Please check your internet connection or if the URL is correct.")
        return

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Locate the table headers
    # The provided HTML snippets indicate that headers have a specific background style.
    # We look for all <td> elements that have 'background: #d9d9d9' in their style attribute.
    header_tds = soup.find_all('td', style=lambda s: s and 'background: #d9d9d9' in s)

    if not header_tds:
        print("Could not find header cells on the page with the expected style.")
        print("The website's structure might have changed. Please inspect the page source.")
        return

    # Extract the text from header cells to form our CSV headers
    headers = [td.get_text(strip=True) for td in header_tds]
    # Filter out empty headers if any (though unlikely with this specific style)
    headers = [h for h in headers if h]

    if not headers:
        print("No valid headers extracted. Check the header cell selection logic.")
        return

    print(f"Found headers: {headers}")

    # Try to find the parent table of one of the header cells
    # This helps ensure we're looking for data within the correct table
    table = header_tds[0].find_parent('table')

    if not table:
        print("Could not find the main table containing the course information.")
        return

    data_rows = []
    # Find all table rows (<tr>) within the identified table
    rows = table.find_all('tr')

    # Iterate through each row to extract data
    for row in rows:
        # We need to distinguish between header rows and data rows.
        # Data rows typically won't have the same specific background style as the headers.
        # We can check if the first cell of the row has the header style.
        first_cell_in_row = row.find('td')
        if first_cell_in_row and 'background: #d9d9d9' in first_cell_in_row.get('style', ''):
            # This is likely a header row, so skip it as headers are already captured.
            continue

        # Extract all <td> elements (data cells) from the current row
        cols = row.find_all('td')

        # Only process rows that have the expected number of columns (or more, we'll slice)
        # and contain actual data (not just empty rows or rows with different structure)
        if len(cols) >= len(headers) and any(col.get_text(strip=True) for col in cols):
            row_data = [col.get_text(strip=True) for col in cols[:len(headers)]]
            data_rows.append(row_data)

    if not data_rows:
        print("No course data rows were found in the table.")
        return

    # Define the full path for the output CSV file
    current_directory = os.getcwd()
    output_path = os.path.join(current_directory, output_csv_filename)

    # Write the extracted data to a CSV file
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(headers)  # Write the header row
            csv_writer.writerows(data_rows) # Write all the data rows
        print(f"\nSuccessfully scraped data and saved to: {output_path}")
    except IOError as e:
        print(f"Error writing data to CSV file '{output_csv_filename}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred while writing the CSV: {e}")

# --- Configuration ---
# The URL of the page you want to scrape
TARGET_URL = 'https://gened.aua.am/courses-and-their-clusters/'
# The name of the CSV file that will be created
CSV_FILE_NAME = 'aua_cluster_scraped.csv'

# --- Run the scraper ---
if __name__ == "__main__":
    scrape_aua_courses(TARGET_URL, CSV_FILE_NAME)