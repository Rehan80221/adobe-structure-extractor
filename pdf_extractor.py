import fitz
import re
import unicodedata
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple

class AdvancedPDFExtractor:
    def __init__(self):
        self.font_size_threshold = 8.0  # Minimum font size to consider
        self.max_heading_length = 200  # Maximum characters for heading
        self.min_heading_length = 2   # Minimum characters for heading
        
        # Text cleaning patterns
        self.noise_patterns = [
            r'^page\s+\d+$',
            r'^figure\s+\d+',
            r'^table\s+\d+',
            r'^appendix\s+[a-z]$',
            r'^\d{1,3}$',  # Standalone numbers
            r'^[^\w\s]*$',  # Only punctuation
        ]
        
        # Title indicators (for title detection)
        self.title_indicators = [
            'title', 'chapter', 'part', 'section', 'introduction',
            'abstract', 'summary', 'overview', 'contents'
        ]
    
    def extract_with_metadata(self, pdf_path: str) -> List[List[Dict[str, Any]]]:
        """
        Extract text with comprehensive metadata from PDF
        Returns: List of pages, each containing list of text elements
        """
        try:
            doc = fitz.open(pdf_path)
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_elements = self._extract_page_elements(page, page_num + 1)
                pages_data.append(page_elements)
            
            doc.close()
            return pages_data
            
        except Exception as e:
            print(f"Error extracting PDF {pdf_path}: {e}")
            return []
    
    def _extract_page_elements(self, page, page_num: int) -> List[Dict[str, Any]]:
        """Extract all text elements from a single page with metadata"""
        elements = []
        
        # Get text blocks with detailed information
        blocks = page.get_text("dict")
        
        for block in blocks.get("blocks", []):
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span.get("text", "").strip()
                    
                    if not text or len(text) < self.min_heading_length:
                        continue
                    
                    # Skip if text is just noise
                    if self._is_noise_text(text):
                        continue
                    
                    element = {
                        'text': self._clean_text(text),
                        'font': span.get('font', ''),
                        'size': round(span.get('size', 0), 1),
                        'flags': span.get('flags', 0),
                        'bbox': span.get('bbox', [0, 0, 0, 0]),
                        'page': page_num,
                        'color': span.get('color', 0),
                        'origin': span.get('origin', [0, 0])
                    }
                    
                    # Add computed properties
                    element.update(self._compute_element_properties(element))
                    elements.append(element)
        
        return elements
    
    def _compute_element_properties(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Compute additional properties for text element"""
        text = element['text']
        bbox = element['bbox']
        
        return {
            'is_bold': bool(element['flags'] & 2**4),
            'is_italic': bool(element['flags'] & 2**1),
            'width': bbox[2] - bbox[0] if bbox else 0,
            'height': bbox[3] - bbox[1] if bbox else 0,
            'x_pos': bbox[0] if bbox else 0,
            'y_pos': bbox[1] if bbox else 0,
            'char_count': len(text),
            'word_count': len(text.split()),
            'is_uppercase': text.isupper() and len(text) > 2,
            'has_numbers': bool(re.search(r'\d', text)),
            'starts_with_number': bool(re.match(r'^\d+\.', text)),
            'is_single_line': '\n' not in text,
            'is_left_aligned': bbox[0] < 100 if bbox else False,
            'is_centered': 200 < bbox[0] < 400 if bbox else False,
            'has_cjk': self._has_cjk_characters(text),
            'language_type': self._detect_language_type(text)
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Normalize Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing punctuation except meaningful ones
        text = re.sub(r'^[^\w\s]+|[^\w\s.!?]+$', '', text)
        
        return text.strip()
    
    def _is_noise_text(self, text: str) -> bool:
        """Check if text is likely noise (headers, footers, page numbers)"""
        text_lower = text.lower().strip()
        
        # Check against noise patterns
        for pattern in self.noise_patterns:
            if re.match(pattern, text_lower):
                return True
        
        # Too short or too long
        if len(text) < self.min_heading_length or len(text) > self.max_heading_length:
            return True
        
        # Mostly punctuation
        if len(re.sub(r'[^\w\s]', '', text)) < len(text) * 0.5:
            return True
        
        return False
    
    def _has_cjk_characters(self, text: str) -> bool:
        """Check if text contains CJK (Chinese, Japanese, Korean) characters"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff' or \
               '\u3040' <= char <= '\u309f' or \
               '\u30a0' <= char <= '\u30ff' or \
               '\uf900' <= char <= '\ufaff':
                return True
        return False
    
    def _detect_language_type(self, text: str) -> str:
        """Detect the primary language type of text"""
        if self._has_cjk_characters(text):
            # More specific CJK detection
            if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
                return 'japanese'
            elif any('\u4e00' <= char <= '\u9fff' for char in text):
                return 'chinese'
            else:
                return 'cjk'
        
        # Check for other scripts
        if any('\u0590' <= char <= '\u05ff' for char in text):
            return 'hebrew'
        elif any('\u0600' <= char <= '\u06ff' for char in text):
            return 'arabic'
        elif any('\u0900' <= char <= '\u097f' for char in text):
            return 'hindi'
        
        return 'latin'
    
    def analyze_font_distribution(self, pages_data: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze font size distribution across the document"""
        font_sizes = []
        font_size_counts = Counter()
        size_to_elements = defaultdict(list)
        
        for page_elements in pages_data:
            for element in page_elements:
                size = element['size']
                if size >= self.font_size_threshold:
                    font_sizes.append(size)
                    font_size_counts[size] += 1
                    size_to_elements[size].append(element)
        
        if not font_sizes:
            return {'sizes': [], 'hierarchy': {}, 'clusters': []}
        
        # Create size clusters
        unique_sizes = sorted(set(font_sizes), reverse=True)
        clusters = self._create_font_clusters(unique_sizes, font_size_counts)
        
        # Create hierarchy mapping
        hierarchy = self._create_font_hierarchy(clusters, size_to_elements)
        
        return {
            'sizes': unique_sizes,
            'counts': dict(font_size_counts),
            'clusters': clusters,
            'hierarchy': hierarchy,
            'size_to_elements': dict(size_to_elements)
        }
    
    def _create_font_clusters(self, sizes: List[float], counts: Counter) -> List[Dict[str, Any]]:
        """Create intelligent font size clusters"""
        if not sizes:
            return []
        
        clusters = []
        
        # Simple clustering based on frequency and size gaps
        for i, size in enumerate(sizes):
            cluster = {
                'size': size,
                'count': counts[size],
                'rank': i + 1,
                'frequency_score': counts[size] / sum(counts.values()),
                'size_score': size / max(sizes) if sizes else 0
            }
            
            # Combined score for importance
            cluster['importance'] = (cluster['size_score'] * 0.7 + 
                                   cluster['frequency_score'] * 0.3)
            
            clusters.append(cluster)
        
        return clusters
    
    def _create_font_hierarchy(self, clusters: List[Dict[str, Any]], 
                              size_to_elements: Dict[float, List[Dict[str, Any]]]) -> Dict[str, float]:
        """Create heading level hierarchy from font clusters"""
        if not clusters:
            return {'title': 16, 'H1': 14, 'H2': 12, 'H3': 10}
        
        # Sort clusters by importance (size + frequency)
        sorted_clusters = sorted(clusters, key=lambda x: x['importance'], reverse=True)
        
        hierarchy = {}
        
        # Assign title (highest importance on first 2 pages)
        title_candidates = []
        for cluster in sorted_clusters[:3]:  # Top 3 clusters
            elements = size_to_elements[cluster['size']]
            early_page_elements = [e for e in elements if e['page'] <= 2]
            if early_page_elements:
                title_candidates.append((cluster['size'], len(early_page_elements)))
        
        if title_candidates:
            # Choose size with most elements on early pages
            hierarchy['title'] = max(title_candidates, key=lambda x: x[1])[0]
        else:
            hierarchy['title'] = sorted_clusters[0]['size']
        
        # Assign heading levels
        remaining_sizes = [c['size'] for c in sorted_clusters if c['size'] != hierarchy['title']]
        
        if len(remaining_sizes) >= 3:
            hierarchy['H1'] = remaining_sizes[0]
            hierarchy['H2'] = remaining_sizes[1]
            hierarchy['H3'] = remaining_sizes[2]
        elif len(remaining_sizes) == 2:
            hierarchy['H1'] = remaining_sizes[0]
            hierarchy['H2'] = remaining_sizes[1]
            hierarchy['H3'] = remaining_sizes[1] - 1  # Slightly smaller
        elif len(remaining_sizes) == 1:
            hierarchy['H1'] = remaining_sizes[0]
            hierarchy['H2'] = remaining_sizes[0] - 1
            hierarchy['H3'] = remaining_sizes[0] - 2
        else:
            # Fallback
            base_size = hierarchy['title'] - 2
            hierarchy['H1'] = base_size
            hierarchy['H2'] = base_size - 1
            hierarchy['H3'] = base_size - 2
        
        return hierarchy