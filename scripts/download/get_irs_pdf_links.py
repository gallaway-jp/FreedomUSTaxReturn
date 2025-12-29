import requests
from bs4 import BeautifulSoup
import csv
import time
import re

def scrape_irs_forms_with_links():
    base_url = "https://www.irs.gov/forms-instructions-and-publications"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    all_forms = []
    
    # First, get the first page to determine total pages
    print("Fetching first page to determine total pages...")
    response = requests.get(base_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find total pages from pagination
    # Look for "Last page" link in pagination
    pagination_links = soup.find_all('a', href=re.compile(r'page='))
    max_page = 0
    for link in pagination_links:
        href = link.get('href', '')
        match = re.search(r'page=(\d+)', href)
        if match:
            page_num = int(match.group(1))
            if page_num > max_page:
                max_page = page_num
    
    total_pages = max_page + 1 if max_page > 0 else 1
    
    print(f"Found {total_pages} pages to scrape")
    
    # Scrape all pages
    for page_num in range(total_pages):
        if page_num == 0:
            url = base_url
        else:
            url = f"{base_url}?page={page_num}"
        
        print(f"Scraping page {page_num + 1}/{total_pages}...")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the table
            table = soup.find('table')
            if not table:
                print(f"No table found on page {page_num + 1}")
                continue
            
            # Find all rows (skip header)
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    # Extract product number (first column often has a link)
                    product_number_cell = cols[0]
                    product_number = product_number_cell.get_text(strip=True)
                    
                    # Try to find PDF link in the first column
                    pdf_link = ''
                    link_tag = product_number_cell.find('a')
                    if link_tag and 'href' in link_tag.attrs:
                        href = link_tag['href']
                        # Make absolute URL if relative
                        if href.startswith('/'):
                            pdf_link = f"https://www.irs.gov{href}"
                        elif href.startswith('http'):
                            pdf_link = href
                        else:
                            pdf_link = f"https://www.irs.gov/{href}"
                    
                    title = cols[1].get_text(strip=True)
                    revision_date = cols[2].get_text(strip=True)
                    posted_date = cols[3].get_text(strip=True)
                    
                    all_forms.append({
                        'Product Number': product_number,
                        'Title': title,
                        'Revision Date': revision_date,
                        'Posted Date': posted_date,
                        'PDF Link': pdf_link
                    })
            
            # Be nice to the server
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error on page {page_num + 1}: {e}")
            continue
    
    # Write to CSV
    output_file = r'C:\Users\Colin\Downloads\irs_forms_with_links.csv'
    
    if all_forms:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Product Number', 'Title', 'Revision Date', 'Posted Date', 'PDF Link'])
            writer.writeheader()
            writer.writerows(all_forms)
        
        print(f"\n✓ Successfully saved {len(all_forms)} forms with PDF links to {output_file}")
    else:
        print("No data found.")

if __name__ == "__main__":
    try:
        scrape_irs_forms_with_links()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
