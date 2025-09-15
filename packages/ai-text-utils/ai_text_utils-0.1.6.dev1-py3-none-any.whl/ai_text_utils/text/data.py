import os
import requests
from bs4 import BeautifulSoup
import re
import time
import json
from pathlib import Path
from tqdm import tqdm

class GutenbergBooks:
    def __init__(self, output_dir="gutenberg_collection"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metadata_file = self.output_dir / "metadata.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Gutenberg-Downloader/1.0'
        })
        self.load_metadata()
    
    def load_metadata(self):
        """Load download metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {"downloaded_books": {}}
    
    def save_metadata(self):
        """Save download metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_book_url(self, book_id):
        """Generate direct HTML file URL for a book"""
        return f"https://www.gutenberg.org/files/{book_id}/{book_id}-h/{book_id}-h.htm"
    
    def download_book(self, book_id, max_retries=3):
        """Download a complete book"""
        # Check if already downloaded
        if str(book_id) in self.metadata["downloaded_books"]:
            print(f"Book {book_id} already downloaded")
            return True
        
        print(f"Downloading book {book_id}...")
        book_url = self.get_book_url(book_id)
        
        for attempt in range(max_retries):
            try:
                text = self.download_html_text(book_url)
                if text:
                    # Save the text
                    output_file = self.output_dir / f"{book_id}.txt"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    # Update metadata
                    self.metadata["downloaded_books"][str(book_id)] = {
                        "url": book_url,
                        "download_date": time.strftime("%Y-%m-%d"),
                        "output_file": str(output_file)
                    }
                    self.save_metadata()
                    
                    print(f"Successfully downloaded book {book_id}")
                    return True
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        
        return False
    
    def download_html_text(self, html_url):
        """Download and extract text from single HTML"""
        try:
            # Download with progress bar
            response = self.session.get(html_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            # Initialize progress bar for download
            block_size = 1024  # 1 Kibibyte
            with tqdm(total=total_size, unit='iB', unit_scale=True, desc="Downloading") as pbar:
                content = b''
                for data in response.iter_content(block_size):
                    content += data
                    pbar.update(len(data))
            
            # Process the downloaded content
            soup = BeautifulSoup(content.decode('utf-8'), 'html.parser')
            
            # Find the main content
            main_content = soup.find('body')
            if not main_content:
                return None
            
            # Clean the HTML
            self.clean_soup(main_content)
            
            # Convert to text
            text = main_content.get_text(separator='\n', strip=True)
            
            # Process the text
            lines = text.split('\n')
            story_start_idx = 0
            story_end_idx = len(lines)
            
            # Find end - look for first occurrence of "END OF ... PROJECT GUTENBERG" in any case
            end_pattern = re.compile(r'END\s+OF\s+.*?PROJECT\s+GUTENBERG', re.IGNORECASE)
            for i, line in enumerate(lines):
                if end_pattern.search(line):
                    story_end_idx = i
                    break
            
            # Find start - look for "START OF ... PROJECT GUTENBERG" pattern
            start_pattern = re.compile(r'START\s+OF\s+.*?PROJECT\s+GUTENBERG', re.IGNORECASE)
            found_start = False
            for i, line in enumerate(lines):
                if start_pattern.search(line):
                    story_start_idx = i + 1  # Start from the next line after the marker
                    found_start = True
                    break
            
            # If we didn't find the start marker, fall back to looking for first substantial chapter
            if not found_start:
                for i in range(len(lines)-1):
                    line = lines[i].strip()
                    next_line = lines[i+1].strip() if i+1 < len(lines) else ""
                    if line.lower().startswith('chapter '):
                        # Check if next line has substantial text (more than just a chapter name)
                        # Look ahead a few lines to find actual content
                        for j in range(i+1, min(i+5, len(lines))):
                            next_text = lines[j].strip()
                            if len(next_text) > 50:  # If we find substantial text
                                story_start_idx = i
                                break
                        if story_start_idx == i:  # If we found our starting point
                            break
            
            # Extract the story content
            story_lines = [line.strip() for line in lines[story_start_idx:story_end_idx]]
            
            # Remove empty lines and make text compact
            # Keep only single newlines between paragraphs
            compact_lines = []
            prev_line_empty = False
            
            for line in story_lines:
                if line.strip():  # If line is not empty
                    compact_lines.append(line)
                    prev_line_empty = False
                elif not prev_line_empty:  # If this is the first empty line
                    compact_lines.append('')  # Add only one empty line
                    prev_line_empty = True
            
            story_text = '\n'.join(compact_lines)
            
            
            return story_text
            
        except Exception as e:
            print(f"Error downloading {html_url}: {e}")
            return None
    
    def clean_soup(self, soup):
        """Remove unwanted elements from BeautifulSoup object"""
        remove_selectors = [
            'script', 'style', 'nav', 'header', 'footer',
            'table', 'form', 'iframe', 'noscript',
            '[class*="menu"]', '[id*="menu"]',
            '[class*="footer"]', '[id*="footer"]',
            '[class*="header"]', '[id*="header"]',
            '[class*="ad"]', '[id*="ad"]'
        ]
        
        for selector in remove_selectors:
            for element in soup.select(selector):
                element.decompose()
    
    def clean_text(self, text):
        """Clean extracted text"""
        import re
        
        # For debugging - print the Unicode values of the first few quotes found
        for i, char in enumerate(text):
            if char in ['â', 'â', '"', '"', '″', '‟', 'â', 'â']:
                print(f"Found quote: {char} (U+{ord(char):04X})")
            if i > 1000:  # Only check first 1000 chars
                break
                
        # Replace smart quotes, dashes, and other problematic characters
        replacements = {
            # Double quotes - Replace all with ASCII " (U+0022)
            '\u2018': '"',  # LEFT SINGLE QUOTATION MARK
            '\u2019': '"',  # RIGHT SINGLE QUOTATION MARK
            '\u201c': '"',  # LEFT DOUBLE QUOTATION MARK
            '\u201d': '"',  # RIGHT DOUBLE QUOTATION MARK
            '\u201e': '"',  # DOUBLE LOW-9 QUOTATION MARK
            '\u201f': '"',  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
            '\u2033': '"',  # DOUBLE PRIME
            '\u301d': '"',  # REVERSED DOUBLE PRIME QUOTATION MARK
            '\u301e': '"',  # DOUBLE PRIME QUOTATION MARK
            '\u301f': '"',  # LOW DOUBLE PRIME QUOTATION MARK
            '\uff02': '"',  # FULLWIDTH QUOTATION MARK
            '\u275d': '"',  # HEAVY DOUBLE TURNED COMMA QUOTATION MARK
            '\u275e': '"',  # HEAVY DOUBLE COMMA QUOTATION MARK
            '\u0022': '"',  # QUOTATION MARK (standard ASCII)
            'â': '"',       # Handle specific encoding of left quote
            'â': '"',       # Handle specific encoding of right quote
            
            # Single quotes - Replace all with ASCII ' (U+0027)
            ''': "'",      # U+2018 LEFT SINGLE QUOTATION MARK
            ''': "'",      # U+2019 RIGHT SINGLE QUOTATION MARK
            '‚': "'",      # U+201A SINGLE LOW-9 QUOTATION MARK
            '‛': "'",      # U+201B SINGLE HIGH-REVERSED-9 QUOTATION MARK
            '′': "'",      # U+2032 PRIME
            '‵': "'",      # U+2035 REVERSED PRIME
            '´': "'",      # U+00B4 ACUTE ACCENT
            '`': "'",      # U+0060 GRAVE ACCENT
            '｀': "'",     # U+FF40 FULLWIDTH GRAVE ACCENT
            '＇': "'",     # U+FF07 FULLWIDTH APOSTROPHE
            '❛': "'",      # U+275B HEAVY SINGLE TURNED COMMA QUOTATION MARK ORNAMENT
            '❜': "'",      # U+275C HEAVY SINGLE COMMA QUOTATION MARK ORNAMENT
            '‹': "'",      # U+2039 SINGLE LEFT-POINTING ANGLE QUOTATION MARK
            '›': "'",      # U+203A SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
            
            # Dashes and hyphens
            '—': '-',      # U+2014 EM DASH
            '–': '-',      # U+2013 EN DASH
            '‒': '-',      # U+2012 FIGURE DASH
            '−': '-',      # U+2212 MINUS SIGN
            '‐': '-',      # U+2010 HYPHEN
            '‑': '-',      # U+2011 NON-BREAKING HYPHEN
            
            # Other characters
            '…': '...',    # U+2026 HORIZONTAL ELLIPSIS
            '\u200b': '',  # ZERO WIDTH SPACE
            '\xa0': ' ',   # NON-BREAKING SPACE
            '¬': '',       # SOFT HYPHEN
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        
        # Remove common artifacts
        text = re.sub(r'\[.*?\]', '', text)  # [Illustration]
        text = re.sub(r'\(.*?\)', '', text)  # (Parenthetical)
        text = re.sub(r'\{.*?\}', '', text)  # {Curly braces}
        
        # Clean up any repeated hyphens (like in "Y-o-u-u")
        text = re.sub(r'(\w)-\s*(?=\w)', r'\1', text)  # Remove hyphens between letters
        
        # Additional quote cleanup - handle any remaining smart quotes
        text = text.encode('ascii', 'ignore').decode('ascii')  # Remove any non-ASCII characters
        
        # Normalize quotes to ensure proper format
        text = re.sub(r'[""〝〞〟‟]', '"', text)  # Normalize any remaining double quotes
        text = re.sub(r'[''‛‚]', "'", text)      # Normalize any remaining single quotes
        
        return text.strip()
    
    def get_book_text(self, book_id):
        """Get text from a book, either from cache or by downloading"""
        book_id = str(book_id).strip()
        file_path = self.output_dir / f"{book_id}.txt"
        
        # If book exists, read it
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # If book doesn't exist, download it
        if self.download_book(book_id):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        return None  # Return None if book couldn't be downloaded

    def _process_book_ids(self, ids_input):
        """
        Process book IDs input that can be either:
        - List of individual book IDs: [123, 105, 90]
        - List of range objects: [{'start_id':108, 'num_books':30}, {'start_id':208, 'num_books':10}]
        """
        result = []
        
        # Check if first item is a dict (range object) or number/string (individual ID)
        if ids_input and isinstance(ids_input[0], dict):
            # Handle range objects
            for range_obj in ids_input:
                start_id = range_obj['start_id']
                num_books = range_obj['num_books']
                result.extend(str(start_id + i) for i in range(num_books))
        else:
            # Handle individual book IDs
            result.extend(str(id) for id in ids_input)
            
        return result

    def get_books(self, book_ids, delay=0.001):
        """
        Get text from multiple books and return combined text.
        
        Args:
            book_ids: Can be either:
                - List of individual book IDs: [123, 105, 90]
                - List of range objects: [{'start_id':108, 'num_books':30}, {'start_id':208, 'num_books':10}]
            delay: Time to wait between downloads
        """
        # Process the book_ids to handle both input formats
        processed_ids = self._process_book_ids(book_ids)
        print(f"Processing {len(processed_ids)} books...")
        
        success_count = 0
        all_texts = []
        
        for book_id in processed_ids:
            # Extract book ID from URL if a URL is provided
            if isinstance(book_id, str) and book_id.startswith('http'):
                book_id = book_id.split('/')[-2]  # Extract ID from URL
            book_id = str(book_id).strip()
            
            text = self.get_book_text(book_id)
            if text:
                all_texts.append(text)
                success_count += 1
            time.sleep(delay)  # Respectful delay between downloads
        
        print(f"\nProcessed {success_count}/{len(processed_ids)} books successfully")
        
        # Combine all texts with separator
        if all_texts:
            return "<end_of_text>".join(all_texts)
        return None


def get_text_from_gutenberg_books(start_book_id=1660, num_books=10, keep_headers=False):
    text=""
    for i in range(num_books):
        id = start_book_id+i
        single_book_txt = download_gutenberg_book(book_id=id,
                                                  output_file="sample"+str(id),
                                                  keep_headers=keep_headers)
        if (single_book_txt is not None):
            text += single_book_txt
    return text

def download_gutenberg_book(book_id,output_file, save_dir="gutenberg_books", keep_headers=False):
    """
    Download a text book from Project Gutenberg by book ID.
    
    Args:
        book_id (str): The Project Gutenberg book ID (e.g., '12345')
        save_dir (str): Directory to save the downloaded book
    """
    # Create save directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Construct URL for the book's text file
    base_url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
    output_file = os.path.join(save_dir, output_file)
    try:

        if not os.path.exists(output_file):
            try:

                # Send request to get the book
                response = requests.get(base_url)
                response.raise_for_status()  # Check for HTTP errors
                
                # Parse HTML to get book title
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.text if soup.title else f"book_{book_id}"
                # Clean title for filename
                title = "".join(c for c in title if c.isalnum() or c in (' ',)).rstrip()

                txt= response.text
                if (txt is not None):
                    if(not keep_headers):
                        txt = compact_gutenberg_text(txt)
                else: 
                    txt=""
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(txt)
                print(f"Downloaded book {book_id} to {output_file}")
                return txt
            except Exception as e:
                print(f"Error downloading book {book_id}: {e}")
        else:
            print(f"File {output_file} already exists. Skipping download.")
            with open(output_file, 'r', encoding='utf-8') as file:
                text = file.read()
                return text
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading book {book_id}: {e}")
        return ""

def compact_gutenberg_text(text):
    """
    Extracts main content from Project Gutenberg eBook and removes excessive newlines
    while preserving paragraph structure.
    """

    # Find main content between standard Gutenberg markers
    start_pattern = re.compile(
        r'\*\*\*\s*START OF (?:THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*',
        re.IGNORECASE | re.DOTALL
    )
    end_pattern = re.compile(
        r'\*\*\*\s*END OF (?:THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*|'
        r'End of (?:the )?Project Gutenberg(?: eBook)?.*',
        re.IGNORECASE | re.DOTALL
    )

    start_match = start_pattern.search(text)
    end_match = end_pattern.search(text)

    if not start_match or not end_match:
        raise ValueError("Could not find Gutenberg start/end markers")

    content = text[start_match.end():end_match.start()]

    # Clean up the content
    # 1. Remove common metadata lines
    content = re.sub(r'^\s*Produced by.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*\[Illustration:.*\]\s*$', '', content, flags=re.MULTILINE)
    
    # 2. Normalize whitespace - compact multiple newlines while preserving paragraphs
    # First replace 3+ newlines with double newline (paragraph break)
    content = re.sub(r'\n{3,}', '\n\n', content)
    # Then replace remaining double newlines with single ones (within paragraphs)
    content = re.sub(r'([^\n])\n{2}([^\n])', r'\1\n\2', content)
    
    # 3. Remove space at start/end of lines
    content = '\n'.join(line.strip() for line in content.split('\n'))
    
    # 4. Remove completely empty lines (but keep single newlines between paragraphs)
    content = re.sub(r'\n\s*\n', '\n\n', content)
    

    return content.strip()
