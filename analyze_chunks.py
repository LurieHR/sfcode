import json

def load_chunks(filename='sf_code_chunks.json'):
    """Load chunks from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)

def find_by_number(data, chunk_number):
    """Find chunk by its chunk_number field - returns (index, chunk)"""
    for i, chunk in enumerate(data):
        if chunk.get('chunk_number') == chunk_number:
            return i, chunk
    return None, None

def get_chunk_summary(chunk):
    """Get important fields of a chunk in a readable format"""
    if not chunk:
        return "Chunk not found"
    
    return {
        'chunk_number': chunk.get('chunk_number'),
        'character_count': chunk.get('character_count'),
        'content': chunk.get('content', '')[:100] + '...' if len(chunk.get('content', '')) > 100 else chunk.get('content', ''),
        'title': chunk.get('title'),
        'chapter': chunk.get('chapter'),
        'article': chunk.get('article'),
        'section_id': chunk.get('section_id'),
        'chunk_index': chunk.get('chunk_index')
    }

def print_chunk_row(chunk, print_header=False):
    """Print a single chunk in table format with HTML tags"""
    if print_header:
        print(f"{'Chunk #':<8} {'Chapter':<25} {'Article':<25} {'Section ID':<20} {'Idx':<3} {'Length':<6} {'HTML Tag Info':<40} {'Text'}")
        print("-" * 150)
    
    chunk_num = chunk.get('chunk_number', 'N/A')
    chapter = str(chunk.get('chapter', 'None'))[:24]
    article = str(chunk.get('article', 'None'))[:24] 
    section_id = str(chunk.get('section_id', 'None'))[:19]
    chunk_idx = chunk.get('chunk_index', 'N/A')
    length = chunk.get('character_count', 0)
    content_preview = repr(str(chunk.get('content', '')))
    
    # Get HTML tag info
    html_tags = chunk.get('html_tags', [])
    tag_info = ""
    if html_tags:
        first_tag = html_tags[0]
        tag_name = first_tag.get('tag', 'N/A')
        classes = first_tag.get('classes', [])
        line_num = first_tag.get('line_number', 'N/A')
        tag_info = f"{tag_name}:{classes}@{line_num}"
    else:
        tag_info = "no_tags"
    
    print(f"    {chunk_num:<8} {chapter:<25} {article:<25} {section_id:<20} {chunk_idx:<3} {length:<6} {tag_info:<40} {content_preview}")

def find_all_short_chunks(filename, max_length):
    """Find and print all chunks shorter than max_length characters in table format"""
    data = load_chunks(filename)
    
    short_chunks = [chunk for chunk in data if chunk['character_count'] <= max_length]
    
    print(f"Found {len(short_chunks)} chunks with <= {max_length} characters:")
    
    for i, chunk in enumerate(short_chunks):
        print_chunk_row(chunk, print_header=(i==0))
    
    return short_chunks

def find_short_chunks(filename, max_length):
    """Find and return all chunks shorter than max_length characters with their indices"""
    data = load_chunks(filename)
    
    short_chunks = []
    for i, chunk in enumerate(data):
        if chunk['character_count'] <= max_length:
            short_chunks.append({
                'array_index': i,
                'chunk_number': chunk.get('chunk_number'),
                'character_count': chunk['character_count'],
                'content': chunk['content'],
                'section_id': chunk.get('section_id'),
                'title': chunk.get('title'),
                'predecessor_length': data[i-1]['character_count'] if i > 0 else None
            })
    
    print(f"Found {len(short_chunks)} chunks with <= {max_length} characters:")
    print("-" * 80)
    
    for chunk in short_chunks:
        chunk_num = chunk['chunk_number'] if chunk['chunk_number'] else 'N/A'
        pred_len = chunk['predecessor_length'] if chunk['predecessor_length'] else 'N/A'
        print(f"Chunk #{chunk_num} (array index {chunk['array_index']})")
        print(f"Length: {chunk['character_count']} | Predecessor length: {pred_len}")
        print(f"Content: '{chunk['content']}'")
        print(f"Title: {chunk['title']}")
        print("-" * 40)
    
    return short_chunks

def print_chunk_details(filename, chunk_numbers):
    """Print full details for specific chunk numbers"""
    data = load_chunks(filename)
    
    for chunk in data:
        chunk_num = chunk.get('chunk_number')
        if chunk_num in chunk_numbers:
            print(f'=== Chunk {chunk_num} ===')
            print(f'Chapter: {chunk.get("chapter")}')
            print(f'Content: {chunk.get("content", "")}')
            print(f'Length: {len(chunk.get("content", ""))}')
            print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze SF code chunks')
    parser.add_argument('-f', '--file', default='sf_code_chunks.json', 
                       help='JSON file to analyze (default: sf_code_chunks.json)')
    parser.add_argument('-s', '--short', type=int, metavar='N',
                       help='Find chunks shorter than N characters')
    parser.add_argument('-n', '--number', type=int, metavar='NUM',
                       help='Analyze chunk by chunk number with neighbors')
    parser.add_argument('--neighbors', type=int, nargs=2, metavar=('CHUNK_NUM', 'RADIUS'),
                       help='Analyze chunks around CHUNK_NUM with RADIUS neighbors on each side')
    parser.add_argument('--chunks', type=int, nargs='+', metavar='CHUNK_NUM',
                       help='Print full details for specific chunk numbers')
    
    args = parser.parse_args()
    
    if args.short:
        find_short_chunks(args.file, args.short)
    elif args.number:
        analyze_chunk_with_neighbors(args.file, args.number)
    elif args.neighbors:
        analyze_neighbors(args.file, args.neighbors[0], args.neighbors[1])
    elif args.chunks:
        print_chunk_details(args.file, args.chunks)
    else:
        print("Use -s to find short chunks, -n to analyze a specific chunk, --neighbors for neighbor analysis, or --chunks for full details")
        print("Example: python analyze_chunks.py -s 10")
        print("Example: python analyze_chunks.py -n 1234")
        print("Example: python analyze_chunks.py --neighbors 1234 2")
        print("Example: python analyze_chunks.py --chunks 25657 25658 25659")

def analyze_chunk_with_neighbors(filename, chunk_number):
    """Analyze a chunk along with its predecessor and successor"""
    data = load_chunks(filename)
    
    array_index, target_chunk = find_by_number(data, chunk_number)
    
    if not target_chunk:
        print(f"Chunk #{chunk_number} not found")
        return
    
    predecessor = data[array_index - 1] if array_index > 0 else None
    successor = data[array_index + 1] if array_index < len(data) - 1 else None
    
    print(f"=== CHUNK #{chunk_number} ANALYSIS ===")
    print(f"Array index: {array_index}")
    print()
    
    if predecessor:
        print("PREDECESSOR:")
        summary = get_chunk_summary(predecessor)
        for key, value in summary.items():
            print(f"  {key}: {value}")
        print()
    
    print("TARGET CHUNK:")
    summary = get_chunk_summary(target_chunk)
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()
    
    if successor:
        print("SUCCESSOR:")
        summary = get_chunk_summary(successor)
        for key, value in summary.items():
            print(f"  {key}: {value}")

def analyze_neighbors(filename, chunk_number, radius):
    """Print info for chunks around target: K-radius, ..., K-1, K, K+1, ..., K+radius"""
    data = load_chunks(filename)
    
    array_index, target_chunk = find_by_number(data, chunk_number)
    
    if not target_chunk:
        print(f"Chunk #{chunk_number} not found")
        return
    
    total_chunks = 2 * radius + 1
    print(f"=== {total_chunks}-CHUNK ANALYSIS AROUND #{chunk_number} (radius={radius}) ===")
    print(f"{'Chunk #':<8} {'Chapter':<25} {'Article':<25} {'Section ID':<20} {'Idx':<3} {'Length':<6} {'HTML Tag Info':<40} {'Text'}")
    print("-" * 150)
    
    for offset in range(-radius, radius + 1):
        idx = array_index + offset
        if 0 <= idx < len(data):
            chunk = data[idx]
            chunk_num = chunk.get('chunk_number', 'N/A')
            chapter = str(chunk.get('chapter', 'None'))[:24]
            article = str(chunk.get('article', 'None'))[:24] 
            section_id = str(chunk.get('section_id', 'None'))[:19]
            chunk_idx = chunk.get('chunk_index', 'N/A')
            length = chunk.get('character_count', 0)
            content_preview = repr(str(chunk.get('content', '')))
            
            # Get HTML tag info
            html_tags = chunk.get('html_tags', [])
            tag_info = ""
            if html_tags:
                first_tag = html_tags[0]
                tag_name = first_tag.get('tag', 'N/A')
                classes = first_tag.get('classes', [])
                line_num = first_tag.get('line_number', 'N/A')
                tag_info = f"{tag_name}:{classes}@{line_num}"
            else:
                tag_info = "no_tags"
            
            marker = " -> " if offset == 0 else "    "
            print(f"{marker}{chunk_num:<8} {chapter:<25} {article:<25} {section_id:<20} {chunk_idx:<3} {length:<6} {tag_info:<40} {content_preview}")
        else:
            marker = " -> " if offset == 0 else "    "
            print(f"{marker}{'N/A':<8} {'N/A':<25} {'N/A':<25} {'N/A':<20} {'N/A':<3} {'N/A':<6} {'N/A':<40} {'N/A'}")

if __name__ == "__main__":
    main()