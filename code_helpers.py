#!/usr/bin/env python3
"""
Helper functions for analyzing San Francisco Municipal Code data.
"""

import json
import re


def count_chunks(json_file):
    """
    Count the total number of chunks in the parsed JSON file.
    
    Args:
        json_file: Path to the JSON file containing chunks
        
    Returns:
        int: Number of chunks, or -1 if error
    """
    try:
        with open(json_file, 'r') as f:
            chunks = json.load(f)
        return len(chunks)
    except Exception as e:
        print(f"Error counting chunks: {e}")
        return -1


def get_chunk_by_identifier(json_file, doc_id=None, section_id=None, uuid=None):
    """
    Retrieve a chunk by its identifier information.
    
    Args:
        json_file: Path to the JSON file containing chunks
        doc_id: Document ID to search for
        section_id: Section ID to search for  
        uuid: UUID to search for
        
    Returns:
        dict: The matching chunk, or None if not found
    """
    try:
        with open(json_file, 'r') as f:
            chunks = json.load(f)
        
        for chunk in chunks:
            if doc_id and chunk.get('doc_id') == doc_id:
                return chunk
            if section_id and chunk.get('section_id') == section_id:
                return chunk
            if uuid and chunk.get('uuid') == uuid:
                return chunk
                
        return None
    except Exception as e:
        print(f"Error retrieving chunk: {e}")
        return None


def count_chapters_and_sections(json_file):
    """
    Count chapters and subsections per chapter in the parsed JSON file.
    
    Args:
        json_file: Path to the JSON file containing chunks
        
    Returns:
        dict: Dictionary with chapter counts and section counts per chapter
    """
    try:
        with open(json_file, 'r') as f:
            chunks = json.load(f)
        
        chapters = {}
        
        for chunk in chunks:
            chapter = chunk.get('chapter')
            if chapter:
                if chapter not in chapters:
                    chapters[chapter] = {
                        'sections': set(),
                        'articles': set(),
                        'divisions': set()
                    }
                
                # Count unique sections
                section_id = chunk.get('section_id')
                if section_id:
                    chapters[chapter]['sections'].add(section_id)
                
                # Count unique articles
                article = chunk.get('article')
                if article:
                    chapters[chapter]['articles'].add(article)
                    
                # Count unique divisions
                division = chunk.get('division')
                if division:
                    chapters[chapter]['divisions'].add(division)
        
        # Convert sets to counts
        result = {
            'total_chapters': len(chapters),
            'chapters': {}
        }
        
        for chapter, data in chapters.items():
            result['chapters'][chapter] = {
                'section_count': len(data['sections']),
                'article_count': len(data['articles']),
                'division_count': len(data['divisions'])
            }
        
        return result
        
    except Exception as e:
        print(f"Error counting chapters and sections: {e}")
        return None


def inspect_chunks(json_file, num_chunks=5, verbose=False):
    """
    Inspect a sample of chunks from the parsed JSON file.
    
    Args:
        json_file: Path to the JSON file containing chunks
        num_chunks: Number of chunks to inspect (default 5)
        verbose: If True, print full content; if False, truncate content
    """
    try:
        with open(json_file, 'r') as f:
            chunks = json.load(f)
        
        print(f"Total chunks: {len(chunks)}")
        print(f"\nInspecting first {min(num_chunks, len(chunks))} chunks:\n")
        
        for i, chunk in enumerate(chunks[:num_chunks]):
            print(f"{'='*80}")
            print(f"CHUNK {i+1}")
            print(f"{'='*80}")
            
            # Print basic metadata
            print(f"Doc ID: {chunk.get('doc_id', 'N/A')}")
            print(f"UUID: {chunk.get('uuid', 'N/A')[:8]}...")
            print(f"Title: {chunk.get('title', 'N/A')}")
            
            # Print hierarchical metadata
            print(f"\nHierarchy:")
            print(f"  Chapter: {chunk.get('chapter', 'N/A')}")
            print(f"  Article: {chunk.get('article', 'N/A')}")
            if chunk.get('article_number'):
                print(f"  Article Number: {chunk.get('article_number')}")
            if chunk.get('article_title'):
                print(f"  Article Title: {chunk.get('article_title')}")
            if chunk.get('division'):
                print(f"  Division: {chunk.get('division')}")
            if chunk.get('section_number'):
                print(f"  Section Number: {chunk.get('section_number')}")
            if chunk.get('section_title'):
                print(f"  Section Title: {chunk.get('section_title')}")
            
            # Print content (truncated unless verbose)
            content = chunk.get('content', '')
            if verbose or len(content) <= 200:
                print(f"\nContent:\n{content}")
            else:
                print(f"\nContent (truncated):\n{content[:200]}...")
            
            # Print links summary
            all_links = chunk.get('all_links', {})
            internal_links = all_links.get('internal_links', [])
            external_links = all_links.get('external_links', [])
            intercode_links = all_links.get('intercode_links', [])
            
            print(f"\nLinks:")
            print(f"  Internal: {len(internal_links)}")
            print(f"  External: {len(external_links)}")
            print(f"  Intercode: {len(intercode_links)}")
            
            # Print history data if present
            history_data = chunk.get('history_data')
            if history_data:
                print(f"\nHistory:")
                if history_data.get('added_by'):
                    print(f"  Added by: {', '.join(history_data['added_by'])}")
                if history_data.get('amended_by'):
                    print(f"  Amended by: {', '.join(history_data['amended_by'])}")
                if history_data.get('see_also'):
                    see_also = history_data['see_also']
                    if len(see_also) > 3:
                        print(f"  See also: {', '.join(see_also[:3])}... ({len(see_also)} total)")
                    else:
                        print(f"  See also: {', '.join(see_also)}")
            
            # Print hash if present
            if chunk.get('hash'):
                print(f"\nHash: {chunk['hash']}")
            
            # Print references if present
            references = chunk.get('references', [])
            if references:
                print(f"\nReferences ({len(references)} total):")
                for i, ref in enumerate(references[:5]):  # Show first 5
                    print(f"  {i+1}. {ref.get('reference_string', 'Unknown')} -> {ref.get('hash', 'No hash')}")
                if len(references) > 5:
                    print(f"  ... and {len(references) - 5} more")
            
            # Print other metadata
            print(f"\nOther metadata:")
            print(f"  Character count: {chunk.get('character_count', 0)}")
            print(f"  Source URL: {chunk.get('source_url', 'N/A')}")
            print(f"  Download date: {chunk.get('download_date', 'N/A')}")
            
            print()
        
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{json_file}': {e}")
    except Exception as e:
        print(f"Error: {e}")


def get_referenced_chunks_from_chunk(json_file, source_chunk, reference_index=None):
    """
    Get the actual chunks that are referenced by a source chunk.
    
    Args:
        json_file: Path to the JSON file containing all chunks
        source_chunk: Already loaded source chunk dictionary
        reference_index: Optional specific reference index to retrieve (0-based)
                        If None, retrieves all referenced chunks
        
    Returns:
        list: List of referenced chunks, or single chunk if reference_index specified
    """
    try:
        # Load all chunks for lookup
        with open(json_file, 'r') as f:
            all_chunks = json.load(f)
        
        # Build hash lookup map for fast access
        hash_map = {}
        for chunk in all_chunks:
            if chunk.get('hash'):
                hash_map[chunk['hash']] = chunk
        
        # Get references from source chunk
        references = source_chunk.get('references', [])
        
        if not references:
            print(f"No references found in chunk: {source_chunk.get('doc_id', 'Unknown')}")
            return []
        
        # If specific index requested
        if reference_index is not None:
            if 0 <= reference_index < len(references):
                ref = references[reference_index]
                target_hash = ref.get('hash')
                if target_hash and target_hash in hash_map:
                    return hash_map[target_hash]
                else:
                    print(f"Referenced chunk not found for hash: {target_hash}")
                    return None
            else:
                print(f"Reference index {reference_index} out of range (0-{len(references)-1})")
                return None
        
        # Get all referenced chunks
        referenced_chunks = []
        for ref in references:
            target_hash = ref.get('hash')
            if target_hash and target_hash in hash_map:
                referenced_chunks.append(hash_map[target_hash])
            else:
                print(f"Warning: Referenced chunk not found for hash: {target_hash}")
        
        return referenced_chunks
        
    except Exception as e:
        print(f"Error getting referenced chunks: {e}")
        return []


if __name__ == "__main__":
    # Example usage:
    # count = count_chunks('test_chunks.json')
    # print(f"Total chunks: {count}")
    
    # chunk = get_chunk_by_identifier('test_chunks.json', doc_id='sf_municipal_code_charter_article_i')
    # if chunk:
    #     print(f"Found chunk: {chunk['title']}")
    
    # stats = count_chapters_and_sections('test_chunks.json')
    # if stats:
    #     print(f"Total chapters: {stats['total_chapters']}")
    
    # source = get_chunk_by_identifier('test_chunks.json', doc_id='sf_municipal_code_preface_to_the_1996_charter_rid-0-0-0-14')
    # referenced = get_referenced_chunks_from_chunk('test_chunks.json', source, reference_index=0)
    # if referenced:
    #     print(f"First reference points to: {referenced['title']}")
    
    pass