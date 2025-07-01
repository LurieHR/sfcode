# SF Municipal Code Parser - TODO List

## README: Parser Overview

### Document Structure
The San Francisco Municipal Code HTML follows a hierarchical structure:
- **Chapter** (e.g., "CHARTER", "ADMINISTRATIVE CODE")
- **Article** (e.g., "ARTICLE I: EXISTENCE AND POWERS")
- **Division** (optional subdivision within articles)
- **Section** (e.g., "SEC. 2.100. COMPOSITION AND SALARY")
- **Subsection** (e.g., "(a)", "(b)", "(c)" - not yet implemented)

### How the Parser Works

1. **Structural Elements Detection**
   - Parser identifies structural dividers by their CSS classes (rbox Chapter, rbox Article, etc.)
   - Each structural element may contain an anchor tag (e.g., `<a name="JD_ArticleI">`) used for navigation

2. **Chunking Strategy**
   - A new chunk is created when:
     - We encounter a structural divider (Chapter, Article, Division, Section)
     - Current content exceeds max_chunk_size (default 2000 chars)
   - Overflow chunks maintain the same metadata as their parent but increment chunk_index

3. **Metadata Extraction**
   - **Hierarchical metadata**: chapter, article, division, section info preserved across chunks
   - **Hash field**: Stores the anchor (e.g., "#JD_ArticleI") for direct navigation
   - **References**: Parsed internal links with target hash and human-readable string
   - **History data**: Amendment/addition info kept with specific chunk where found
   - **Links**: Internal, external, and intercode links accumulated per section

4. **Chunk Identification**
   - **doc_id**: Hierarchical path (e.g., "sf_municipal_code_charter_article_i_rid-0-0-0-18")
   - **chunk_id**: doc_id + chunk_index (e.g., "sf_municipal_code_charter_article_i_rid-0-0-0-18_1")
   - **chunk_index**: Starts at 1 for each section, increments for overflow chunks
   - **uuid**: Deterministic UUID based on doc_id

5. **Content Processing**
   - Normal-Level divs contain the actual text content
   - Text is extracted and cleaned, removing HTML but preserving structure
   - Multiple Normal-Level divs are concatenated with double newlines

### Key Files
- `parse_sf_code.py`: Main parser implementation
- `code_helpers.py`: Helper functions for analysis and chunk retrieval
- `rawcodes/san_francisco-ca-complete.html`: Source HTML file

## TODO

### High Priority
- [ ] REFACTOR: Change parser to process ALL elements, not just rbox - never throw away visible text
  - Process every element in the HTML
  - Extract text from ALL elements
  - Use classes for structure/metadata but never skip text
  - Core principle: If it's visible in browser, it must be in the chunk
- [ ] Extract Subsection references from class='Subsection toc-destination rbox' (1560 instances)
- [ ] Create cross-reference resolver to map internal links to chunk IDs for Elasticsearch navigation
- [ ] Extract text from "rbox level-Article" elements (82 instances) - currently skipped
- [ ] Extract text from "rbox level-Year" elements (15 instances) - currently skipped
- [ ] Extract text from "rbox level-Code" elements (9 instances) - currently skipped
- [ ] Extract text from "rbox List" elements (1 instance) - currently skipped
- [ ] Parse non-rbox elements that contain visible text (parser currently only processes rbox elements)

### Medium Priority
- [ ] Extract Editor's Notes from class='EdNote' separately for editorial context (868 instances)
- [ ] Extract Code section identifiers from class='CodeSecs' (2438 instances)
- [ ] Extract table structure from class='Table-Text' (31081 instances)
- [ ] Extract NotCodified sections (7766 instances)
- [ ] Extract PRHeader content (1308 instances)
- [ ] Extract History headers from class='History-Header' (1027 instances)
- [ ] Extract Chapter annotations from class='ChapAn' (23562 instances)
- [ ] Extract subsection structure (a), (b), (c) numbered items  
- [ ] Extract non-Web <a> tags (other link types)
- [ ] Extract parenthetical cross-references in regular text
- [ ] Extract 'See' references in regular text (not just History)

### Low Priority
- [ ] Extract formatting (Italics, bold, etc.) - 3288 Italics instances
- [ ] Extract AnnotationDrawer recordid attributes  
- [ ] Extract styling metadata (bold, italic formatting indicators)
- [ ] Extract all element IDs and classes beyond main rbox

## Notes
Term definitions appear as `<span style="font-weight: bold;font-style: italic;">Term Name</span>` followed by definition text.

Editor's Notes contain important cross-references like "See Interpretations related to this Section."

Section numbers follow patterns like "SEC. 141." or "Sec. 101.1" and help identify document structure.

Cross-reference resolver will enable clicking on internal links in search results to jump directly to referenced sections.