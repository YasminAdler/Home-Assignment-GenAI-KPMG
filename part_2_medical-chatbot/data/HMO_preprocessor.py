import os
from bs4 import BeautifulSoup
from collections import defaultdict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for HMOs
HMOS_HEBREW = ["מכבי", "מאוחדת", "כללית"]
HMO_NAME_MAPPING = {
    "מכבי": "maccabi",
    "מאוחדת": "meuhedet",
    "כללית": "clalit"
}

def preprocess_hmo_html(input_dir: str, output_dir: str):
    """
    Preprocess multiple HTML files containing HMO service tables.
    Aggregates services per HMO into combined HTML files.

    Args:
        input_dir: Directory containing the raw service HTML files
        output_dir: Directory to save the per-HMO combined HTML files
    """
    os.makedirs(output_dir, exist_ok=True)

    hmo_data = defaultdict(list)
    processed_files = 0
    processed_services = 0

    for filename in os.listdir(input_dir):
        if not filename.endswith(".html"):
            continue
        filepath = os.path.join(input_dir, filename)
        
        logger.info(f"Processing file: {filename}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")

            # Extract title from filename to use as section name
            section_title = filename.replace(".html", "").replace("_", " ")
            logger.info(f"Extracted section title: {section_title}")

            # Find all tables in the document
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} tables in {filename}")

            for table_idx, table in enumerate(tables):
                header = table.find('tr')
                if not header:
                    continue
                
                # Extract column headers
                columns = [th.get_text(strip=True) for th in header.find_all('th')]
                logger.info(f"Table {table_idx+1} columns: {columns}")
                
                if len(columns) < 4:
                    logger.warning(f"Table {table_idx+1} has fewer than 4 columns, skipping")
                    continue
                
                # Process each row in the table
                rows = table.find_all('tr')[1:]  # Skip header row
                logger.info(f"Processing {len(rows)} rows from table {table_idx+1}")
                
                for row_idx, row in enumerate(rows):
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue
                    
                    # Extract service name from first column
                    service_name = cells[0].get_text(strip=True)
                    
                    # Extract relevant HMO data
                    for i, hmo in enumerate(HMOS_HEBREW):
                        if i + 1 >= len(cells):
                            continue
                            
                        # Get the complete HTML content of the cell
                        benefit_html = cells[i + 1].decode_contents()
                        
                        # Add more structure to make specific data easier to find
                        formatted_section = f"""
                        <div class="service-section" id="{section_title.lower().replace(' ', '-')}-{service_name.lower().replace(' ', '-')}">
                            <h3>{section_title} - {service_name}</h3>
                            <div class="benefit-details">
                                {benefit_html}
                            </div>
                        </div>
                        """
                        
                        hmo_data[hmo].append(formatted_section)
                        processed_services += 1
                    
                    if row_idx < 3:  # Log the first few rows as samples
                        logger.info(f"Processed service: {service_name}")
        
            processed_files += 1
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")

    # Write the aggregated content to files
    for hmo, sections in hmo_data.items():
        file_path = os.path.join(output_dir, f"{HMO_NAME_MAPPING[hmo]}.html")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{hmo} Healthcare Services</title>
                <meta name="description" content="Healthcare services information for {hmo}">
            </head>
            <body>
                <h1>{hmo} Healthcare Services Information</h1>
                <div class="services-container">
                    {"".join(sections)}
                </div>
            </body>
            </html>
            """)
        
        logger.info(f"Created knowledge base file for {hmo} with {len(sections)} services")

    logger.info(f"Preprocessing complete. Processed {processed_files} files and {processed_services} services.")
    return f"Preprocessing complete. Files saved to {output_dir}"