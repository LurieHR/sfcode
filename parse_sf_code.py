#!/usr/bin/env python3
"""
Parse San Francisco Municipal Code HTML and create chunked dictionaries with metadata.
"""

import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json
import sys
from datetime import datetime, timezone
import argparse

# Configuration
CONFIG = {
    'input_file': 'rawcodes/san_francisco-ca-complete.html',
    'output_file': 'sf_code_chunks.json',
    'max_chunk_size': 2000,
    'congressionalrag_path': '/Users/helen/hack/git/congressionalrag'
}

# Add the congressionalrag helpers to path
sys.path.append(CONFIG['congressionalrag_path'])
from helpers.helpers import generate_doc_uuid

class SFCodeParser:
    def __init__(self, html_file: str, max_chunk_size: int = 2000):
        self.html_file = html_file
        self.max_chunk_size = max_chunk_size
        self.chunks = []
        
    def _reset_metadata_for_new_section(self, metadata: Dict[str, Any], hierarchy_tags: List[Dict], 
                                        current_level_index: int) -> None:
        """Reset metadata fields for a new section while preserving hierarchy above current level."""
        # Reset accumulating fields
        metadata['all_links'] = {'internal_links': [], 'external_links': [], 'intercode_links': [], 'image_links': []}
        metadata['history_data'] = {'added_by': [], 'amended_by': [], 'see_also': []}
        metadata['references'] = []
        metadata['hash'] = None
        metadata['chunk_index'] = 1  # Reset to 1 for new section
        metadata['div_classes'] = []  # Reset div classes for new section
        
        # Reset all fields at and below current level
        for i in range(current_level_index, len(hierarchy_tags)):
            for field in hierarchy_tags[i]['fields']:
                metadata[field] = None
    
    def parse_text_only_no_metadata(self) -> List[Dict[str, Any]]:
        """Parse HTML file extracting only text content without links, images, or other metadata."""
        
        try:
            with open(self.html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
        except FileNotFoundError:
            print(f"Error: File '{self.html_file}' not found")
            return []
        except Exception as e:
            print(f"Error reading file '{self.html_file}': {e}")
            return []
        
        # Static metadata
        static_metadata = {
            'source_url': 'https://codelibrary.amlegal.com/codes/san_francisco/latest/overview',
            'download_date': '2024-06-30',
            'city': 'San Francisco'
        }
        
        current_text = ""
        current_metadata = {
            'chapter': None,
            'article': None, 
            'article_number': None,
            'article_title': None,
            'division': None,
            'section': None,
            'section_number': None,
            'section_id': None,
            'subsection': None,
            'chunk_index': 1,
            'div_classes': [],
            'all_links': {'internal_links': [], 'external_links': [], 'intercode_links': [], 'image_links': []},
            'history_data': {'added_by': [], 'amended_by': [], 'see_also': []},
            'references': []
        }
        
        # Define structural boundaries that trigger new chunks
        # Each tuple contains the required classes for that structural type
        structural_patterns = {
            ('rbox', 'Chapter'): 'chapter',
            ('rbox', 'Article'): 'article',
            ('rbox', 'Division'): 'division',
            ('Section', 'toc-destination'): 'section',
            ('Subsection', 'toc-destination'): 'subsection'
        }
        
        # Process elements but only extract their direct text (like browser rendering)
        for element in soup.descendants:
            # We want NavigableString objects (text nodes) only
            if not isinstance(element, str):
                continue
                
            # Skip whitespace-only text
            text = element.strip()
            if not text:
                continue
                
            # Skip text inside script/style tags
            parent = element.parent
            if parent.name in ['script', 'style']:
                continue
                
            # Get the closest parent element with meaningful structure
            structural_parent = parent
            while structural_parent and not structural_parent.get('class'):
                structural_parent = structural_parent.parent
                if not structural_parent or structural_parent.name == 'html':
                    break
                    
            # Check if this is a structural boundary
            element_classes = set(structural_parent.get('class', [])) if structural_parent and hasattr(structural_parent, 'get') else set()
            structural_type = None
            
            for required_classes, field_name in structural_patterns.items():
                if all(cls in element_classes for cls in required_classes):
                    structural_type = field_name
                    break
            
            if structural_type:
                # Save current chunk if it has content
                if current_text:
                    self._save_chunk(current_text, current_metadata, static_metadata)
                    current_text = ""
                    current_metadata['chunk_index'] = 1  # Reset to 1 for new section
                    current_metadata['div_classes'] = []  # Reset div classes for new section
                
                # Update metadata
                current_metadata[structural_type] = text
                
                # TODO: Extract additional metadata (section numbers, article titles, etc.)
                # TODO: Implement hierarchical reset based on level
                
                # Start new chunk with structural text
                current_text = text
            else:
                # Not structural, add to current chunk
                if current_text:
                    current_text += "\n\n" + text
                else:
                    current_text = text
                    
                # Track div classes if present (from the structural parent)
                if element_classes:
                    div_class = ' '.join(sorted(element_classes))  # Sort for consistency
                    if div_class not in current_metadata['div_classes']:
                        current_metadata['div_classes'].append(div_class)
                        
                # Check for ID that might be section_id (from the parent element)
                if parent and hasattr(parent, 'get') and parent.get('id'):
                    current_metadata['section_id'] = parent.get('id')
        
        # Save final chunk
        if current_text:
            self._save_chunk(current_text, current_metadata, static_metadata)
            
        print(f"Created {len(self.chunks)} chunks")
        return self.chunks
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse the HTML file and return chunked data with metadata."""
        
        with open(self.html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Find all rbox elements that contain structural information
        elements = soup.find_all('div', class_=re.compile(r'rbox'))
        print(f"Found {len(elements)} rbox elements")
        
        # Hard-coded metadata fields
        static_metadata = {
            'source_url': 'https://codelibrary.amlegal.com/codes/san_francisco/latest/overview',
            'download_date': '2024-06-30',
            'city': 'San Francisco'
        }
        
        current_text = ""
        current_metadata = {
            'chapter': None,
            'article': None, 
            'article_number': None,
            'article_title': None,
            'division': None,
            'section_id': None,
            'section_number': None,
            'section_title': None,
            'subsection': None,
            'chunk_index': 1,  # Track chunk index within section (starts at 1)
            'div_classes': [],  # Track CSS classes of content divs in this chunk
            'all_links': {'internal_links': [], 'external_links': [], 'intercode_links': [], 'image_links': []},
            'history_data': {'added_by': [], 'amended_by': [], 'see_also': []},
            'references': []
        }
        
        # Define hierarchy tags with extraction rules
        hierarchy_tags = [
            {
                'tag': 'rbox Chapter', 
                'type': 'Chapter', 
                'fields': ['chapter'],
                'extractors': {}
            },
            {
                'tag': 'rbox Article', 
                'type': 'Article', 
                'fields': ['article', 'article_number', 'article_title'],
                'extractors': {
                    'article_number': r'^(\d+[A-Z]?-?\d*\.?|\b[IVXLCDM]+\b)\.?\s+(.+)',
                    'article_title': lambda match: match.group(2) if match else None
                }
            },
            {
                'tag': 'rbox Division', 
                'type': 'Division', 
                'fields': ['division'],
                'extractors': {}
            },
            {
                'tag': 'Section toc-destination', 
                'type': 'Section', 
                'fields': ['section_title', 'section_number'],
                'extractors': {
                    'section_number': r'SEC\.\s*(\d+\.?\d*)'
                }
            },
            {
                'tag': 'Subsection toc-destination', 
                'type': 'Subsection', 
                'fields': ['subsection'],
                'extractors': {}
            }
        ]
        
        for i, element in enumerate(elements):
            if i % 100 == 0:
                print(f"Processing element {i}/{len(elements)}")
                
            class_name = ' '.join(element.get('class', []))
            element_id = element.get('id', '')
            
            # Skip AnnotationDrawer and get content div
            content_div = element
            annotation_drawer = element.find('AnnotationDrawer')
            if annotation_drawer:
                # Get the div after AnnotationDrawer
                content_divs = element.find_all('div', recursive=False)
                if len(content_divs) > 1:
                    content_div = content_divs[1]
                elif len(content_divs) == 1:
                    content_div = content_divs[0]
            
            # Extract text from the content div, avoiding nested rbox elements
            text_content = ""
            if content_div != element or not annotation_drawer:
                # Process all descendants but skip nested rbox elements
                for desc in content_div.descendants:
                    if isinstance(desc, str):
                        text = desc.strip()
                        if text:
                            # Check if this text is inside a nested rbox
                            parent = desc.parent
                            is_nested_rbox = False
                            while parent and parent != content_div:
                                if hasattr(parent, 'get') and parent.get('class'):
                                    if 'rbox' in parent.get('class', []):
                                        is_nested_rbox = True
                                        break
                                parent = parent.parent
                            
                            if not is_nested_rbox:
                                text_content += text + " "
            text_content = text_content.strip()
            
            # Check if this is any structural element
            structural_match = None
            for hier in hierarchy_tags:
                if hier['tag'] in class_name:
                    structural_match = hier
                    break
            
            if structural_match:
                # Save current chunk if exists
                if current_text:
                    self._save_chunk(current_text, current_metadata, static_metadata)
                    current_text = ""
                
                # Find current level index
                current_level_index = hierarchy_tags.index(structural_match)
                
                # Reset metadata using helper function
                self._reset_metadata_for_new_section(current_metadata, hierarchy_tags, current_level_index)
                
                # Extract element text (already extracted as text_content above)
                element_text = text_content
                
                # Extract data using the configuration
                extracted_data = self._extract_structural_data(element, structural_match)
                
                # Update current metadata with extracted data
                current_metadata.update(extracted_data)
                
                # Set hash based on the anchor found using data-driven approach
                anchor_field = f"{structural_match['type'].lower()}_anchor"
                if anchor_field in extracted_data:
                    current_metadata['hash'] = f"#{extracted_data[anchor_field]}"
                
                # Start new chunk with the structural element's text
                if text_content:
                    current_text = text_content
                
                
            # No changes needed here - text extraction happens above
            
            elif 'Normal-Level' in class_name:
                # This is content - add to current chunk
                if text_content:
                    # Extract the inner div's class for semantic information
                    inner_div = element.find('div', recursive=False)
                    if inner_div and inner_div.find('annotationdrawer'):
                        # Skip AnnotationDrawer and get the actual content div
                        content_divs = element.find_all('div', recursive=False)
                        if len(content_divs) > 1:
                            inner_div = content_divs[1]
                    
                    if inner_div and inner_div.get('class'):
                        div_class = ' '.join(inner_div.get('class', []))
                        if div_class and div_class not in current_metadata['div_classes']:
                            current_metadata['div_classes'].append(div_class)
                    
                    # Extract and accumulate all types of links and metadata from this element
                    all_links = self.div_links_extract_all(element)
                    history_data = self.div_history_extract(element)
                    
                    # Store raw internal links
                    current_metadata['all_links']['internal_links'].extend(all_links['internal_links'])
                    current_metadata['all_links']['external_links'].extend(all_links['external_links']) 
                    current_metadata['all_links']['intercode_links'].extend(all_links['intercode_links'])
                    current_metadata['all_links']['image_links'].extend(all_links.get('image_links', []))
                    
                    # Parse internal links to extract reference information
                    self._process_internal_links(all_links['internal_links'], current_metadata)
                    
                    # Store history data only if present in this specific div
                    # This keeps history contextually relevant to where it appears
                    if any(history_data[key] for key in history_data):
                        current_metadata['history_data'] = history_data
                    
                    # Check if adding this would exceed chunk size
                    if len(current_text + text_content) > self.max_chunk_size:
                        # Save current chunk and start new one
                        if current_text:
                            self._save_chunk(current_text, current_metadata, static_metadata)
                            current_metadata['chunk_index'] += 1  # Increment for next chunk
                        current_text = text_content
                    else:
                        current_text += "\n\n" + text_content if current_text else text_content
                    
                    # Update section_id from element id
                    if element_id:
                        current_metadata['section_id'] = element_id
        
        # Save final chunk
        if current_text:
            self._save_chunk(current_text, current_metadata, static_metadata)
            
        print(f"Created {len(self.chunks)} chunks")
        return self.chunks
    
    def _process_internal_links(self, internal_links: List[str], metadata: Dict[str, Any]) -> None:
        """Process internal links and add them to metadata references."""
        for link in internal_links:
            # Parse the full link information
            link_info = self.parse_internal_link(link)
            
            # Get the human-readable reference string
            ref_string = self.parse_internal_hierarchy_ref(link)
            
            # Store the parsed reference
            if link_info['hash']:
                reference = {
                    'hash': link_info['hash'],
                    'reference_string': ref_string if ref_string else link_info['record_id'],
                    'record_id': link_info['record_id']
                }
                metadata['references'].append(reference)
    
    def _extract_structural_data(self, element, hier_config):
        """Extract data from a structural element using configuration rules."""
        data = {}
        
        # Get the content div (the one after AnnotationDrawer)
        content_div = element.find('div', recursive=False)
        if content_div and content_div.find('annotationdrawer'):
            # Skip the AnnotationDrawer div and get the next one
            content_divs = element.find_all('div', recursive=False)
            if len(content_divs) > 1:
                content_div = content_divs[1]
            else:
                content_div = None
        
        if not content_div:
            return data
            
        # Extract text content (use same approach as main parser)
        element_text = ""
        for desc in content_div.descendants:
            if isinstance(desc, str):
                text = desc.strip()
                if text:
                    # Check if this text is inside a nested element we should skip
                    parent = desc.parent
                    skip = False
                    while parent and parent != content_div:
                        if hasattr(parent, 'name') and parent.name in ['annotationdrawer', 'a']:
                            skip = True
                            break
                        parent = parent.parent
                    
                    if not skip:
                        element_text += text + " "
        element_text = element_text.strip()
        
        # Extract anchor if present
        anchor_element = content_div.find('a', {'name': re.compile(r'JD_.*')})
        if anchor_element:
            anchor_field = f"{hier_config['type'].lower()}_anchor"
            data[anchor_field] = anchor_element.get('name', '')
        
        # Set the main field (first field in the list)
        if hier_config['fields']:
            data[hier_config['fields'][0]] = element_text
        
        # Apply extractors if defined
        if 'extractors' in hier_config:
            for field, extractor in hier_config['extractors'].items():
                if isinstance(extractor, str):
                    # It's a regex pattern
                    match = re.search(extractor, element_text, re.IGNORECASE)
                    if match:
                        if field == 'section_number':
                            data[field] = match.group(1)
                        elif field == 'article_number':
                            data[field] = match.group(1)
                            # Check if there's a title extractor
                            if 'article_title' in hier_config['extractors']:
                                title_extractor = hier_config['extractors']['article_title']
                                if callable(title_extractor):
                                    data['article_title'] = title_extractor(match)
                        else:
                            data[field] = match.group(1) if match.lastindex else match.group(0)
                elif callable(extractor):
                    # It's a function - this is handled above for article_title
                    pass
        
        # Default article_title if not extracted
        if hier_config['type'] == 'Article' and 'article_title' not in data:
            data['article_title'] = element_text
            
        return data
    
    def parse_internal_link(self, link_str):
        """Parse internal link to extract all components."""
        # Extract pathname
        pathname_match = re.search(r"pathname: '([^']+)'", link_str)
        pathname = pathname_match.group(1) if pathname_match else None
        
        # Extract hash
        hash_match = re.search(r"hash: '(#[^']+)'", link_str)
        hash_val = hash_match.group(1) if hash_match else None
        
        # Extract the record ID from pathname (e.g., 0-0-0-18 from the pathname)
        record_id = None
        if pathname:
            parts = pathname.split('/')
            if len(parts) > 0:
                record_id = parts[-1]  # Get the last part which should be the record ID
        
        return {
            'pathname': pathname,
            'hash': hash_val,
            'record_id': record_id,
            'full_link': link_str
        }
    
    def parse_internal_hierarchy_ref(self, link_str):
        """Parse internal link to extract hierarchy reference."""
        # Extract hash from link string
        hash_match = re.search(r"hash: '#(JD_[^']+)'", link_str)
        if not hash_match:
            return None
            
        jd_ref = hash_match.group(1).replace('JD_', '')
        
        # Categorize and format the reference
        if jd_ref.startswith('Article'):
            # Extract article number (Roman or Arabic)
            article_match = re.match(r'Article([IVXLCDM]+|[\d\w-]+)', jd_ref)
            if article_match:
                return f"Article {article_match.group(1)}"
        elif re.match(r'^A\d', jd_ref):
            # Appendix section reference (e.g., A8.343)
            return f"Section {jd_ref}"
        elif re.match(r'^\d', jd_ref):
            # Regular section reference
            return f"Section {jd_ref}"
        elif jd_ref.startswith('Appendix'):
            # Full appendix reference
            return jd_ref
        else:
            # Other references (Chapter names, etc.)
            return jd_ref
    
    def div_history_extract(self, element):
        """Extract structured history from History divs."""
        history_data = {
            'added_by': [],
            'amended_by': [],
            'see_also': []
        }
        
        history_divs = element.find_all('div', class_='History')
        for history_div in history_divs:
            history_text = history_div.get_text(strip=True)
            
            # Extract "Added by" ordinances
            added_match = re.search(r'Added by\s+(.*?)(?:;|$)', history_text, re.IGNORECASE)
            if added_match:
                added_text = added_match.group(1)
                # Find ordinance numbers in this text
                ord_matches = re.findall(r'Ord\.?\s*([^;\s,)]+)', added_text)
                history_data['added_by'].extend(ord_matches)
            
            # Extract "Amended by" ordinances  
            amended_match = re.search(r'Amended by\s+(.*?)(?:;|$)', history_text, re.IGNORECASE)
            if amended_match:
                amended_text = amended_match.group(1)
                # Find ordinance numbers in this text
                ord_matches = re.findall(r'Ord\.?\s*([^;\s,)]+)', amended_text)
                history_data['amended_by'].extend(ord_matches)
            
            # Extract "see" references
            see_matches = re.findall(r'see\s+([^;)]+)', history_text, re.IGNORECASE)
            history_data['see_also'].extend(see_matches)
        
        return history_data
    
    def div_links_extract_all(self, element):
        """Extract all types of links from an element."""
        # Internal links (Jump links within SF Municipal Code)
        internal_links = []
        link_elements = element.find_all(['Link', 'link'])
        for link in link_elements:
            to_attr = link.get('to', '')
            if to_attr:
                internal_links.append(to_attr)
        
        # External links (ordinance PDFs, websites)
        external_links = []
        a_elements = element.find_all('a', class_='Web')
        for a in a_elements:
            href = a.get('href', '')
            text = a.get_text(strip=True)
            if href:
                external_links.append({'href': href, 'text': text})
        
        # Intercode links (references to other municipal codes)
        intercode_links = []
        intercode_elements = element.find_all('intercodelink')
        for intercode in intercode_elements:
            destination_id = intercode.get('destinationid', '')
            text = intercode.get_text(strip=True)
            if destination_id:
                intercode_links.append({'destination_id': destination_id, 'text': text})
        
        # Image links
        image_links = []
        img_elements = element.find_all('img')
        for img in img_elements:
            src = img.get('src', '')
            alt = img.get('alt', '')
            width = img.get('width', '')
            height = img.get('height', '')
            if src:
                image_links.append({
                    'src': src,
                    'alt': alt,
                    'width': width,
                    'height': height
                })
        
        return {
            'internal_links': internal_links,
            'external_links': external_links,
            'intercode_links': intercode_links,
            'image_links': image_links
        }
    
    def _save_chunk(self, text: str, metadata: Dict[str, Any], static_metadata: Dict[str, str]):
        """Save a chunk with its metadata in the standard document format."""
        # Create hierarchical title
        title_parts = []
        if metadata['chapter']:
            title_parts.append(metadata['chapter'])
        if metadata['article']:
            title_parts.append(metadata['article'])
        if metadata['division']:
            title_parts.append(metadata['division'])
        
        title = " - ".join(title_parts) if title_parts else "San Francisco Municipal Code Section"
        
        # Create doc_id (descriptive identifier for this section)
        doc_id_parts = ["sf_municipal_code"]
        if metadata['chapter']:
            doc_id_parts.append(metadata['chapter'].lower().replace(' ', '_').replace(':', ''))
        if metadata['article']:
            doc_id_parts.append(metadata['article'].lower().replace(' ', '_').replace(':', ''))
        if metadata['section_id']:
            doc_id_parts.append(metadata['section_id'])
        
        doc_id = "_".join(doc_id_parts)
        
        # Generate deterministic UUID
        doc_uuid = generate_doc_uuid(doc_id)
        
        # Remove the topic logic for now
        
        # chunk_index must be present - error if missing
        if 'chunk_index' not in metadata:
            raise ValueError(f"chunk_index missing from metadata for doc_id: {doc_id}")
            
        chunk = {
            **metadata,  # Include ALL metadata fields
            **static_metadata,  # Include ALL static metadata fields
            'content': text,
            'doc_id': doc_id,
            'chunk_id': f"{doc_id}_{metadata['chunk_index']}",
            'chunk_index': metadata['chunk_index'],
            'title': title,
            'uuid': doc_uuid,
            'processing_timestamp': datetime.now(timezone.utc).isoformat(),
            'character_count': len(text)
        }
        self.chunks.append(chunk)
    
    
    def save_to_json(self, output_file: str):
        """Save chunks to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)

def main():
    # Parse command-line arguments
    parser_args = argparse.ArgumentParser(description='Parse San Francisco Municipal Code HTML files')
    parser_args.add_argument('-i', '--input', default=CONFIG['input_file'], 
                            help=f"Input HTML file (default: {CONFIG['input_file']})")
    parser_args.add_argument('-o', '--output', default=CONFIG['output_file'],
                            help=f"Output JSON file (default: {CONFIG['output_file']})")
    parser_args.add_argument('-s', '--chunk-size', type=int, default=CONFIG['max_chunk_size'],
                            help=f"Maximum chunk size (default: {CONFIG['max_chunk_size']})")
    parser_args.add_argument('-b', '--browse', action='store_true',
                            help="Browse chunks interactively after parsing")
    args = parser_args.parse_args()
    
    # Parse the file
    print(f"Parsing {args.input}...")
    parser = SFCodeParser(args.input, max_chunk_size=args.chunk_size)
    chunks = parser.parse()
    
    if args.browse:
        print(f"\nBrowsing {len(chunks)} chunks (10 at a time, press Enter to continue):")
        
        for i in range(0, len(chunks), 10):
            batch = chunks[i:i+10]
            print(f"\n{'='*80}")
            print(f"CHUNKS {i+1}-{min(i+10, len(chunks))} of {len(chunks)}")
            print('='*80)
            
            for j, chunk in enumerate(batch):
                chunk_num = i + j + 1
                chapter = str(chunk.get('chapter', 'None'))[:30]
                article = str(chunk.get('article', 'None'))[:30]
                division = str(chunk.get('division', 'None'))[:30]
                section_id = str(chunk.get('section_id', 'None'))[:20]
                char_count = chunk.get('character_count', 0)
                
                print(f"**** [{chunk_num:3}] Ch:{chapter} | Art:{article} | Div:{division} | Sec:{section_id} | Chars:{char_count}")
                print(f"CONTENT:")
                print(chunk.get('content', ''))
                print()
            
            if i + 10 < len(chunks):
                input("Press Enter to continue to next 10 chunks...")
    
    parser.save_to_json(args.output)
    print(f"Saved {len(chunks)} chunks to {args.output}")

if __name__ == "__main__":
    main()