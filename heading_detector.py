"""
Smart Heading Detection and Classification Module
Multi-signal approach for accurate heading level detection
"""

import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter

class SmartHeadingDetector:
    def __init__(self):
        # Confidence thresholds
        self.min_confidence = 0.4
        self.title_confidence = 0.6
        
        # Heading patterns (language-agnostic)
        self.heading_patterns = [
            r'^\d+\.?\s+',                    # "1. " or "1 "
            r'^\d+\.\d+\.?\s+',              # "1.1. " or "1.1 "
            r'^\d+\.\d+\.\d+\.?\s+',         # "1.1.1. "
            r'^[A-Z]+\.?\s+',                # "CHAPTER "
            r'^[IVX]+\.?\s+',                # Roman numerals "I. "
            r'^[a-z]\)?\s+',                 # "a) " or "a "
            r'^\([a-z]\)\s+',                # "(a) "
            r'^\([0-9]\)\s+',                # "(1) "
        ]
        
        # CJK heading patterns
        self.cjk_patterns = [
            r'^第[一二三四五六七八九十\d]+章',      # Chinese chapter
            r'^第[一二三四五六七八九十\d]+節',      # Chinese section
            r'^第[一二三四五六七八九十\d]+条',      # Japanese article
            r'^[１２３４５６７８９０]+[．。]\s*',     # Full-width numbers
            r'^[一二三四五六七八九十]+[、．。]\s*',   # Chinese numerals
        ]
        
        # Title indicators
        self.title_keywords = {
            'latin': ['title', 'chapter', 'part', 'section', 'introduction', 
                     'abstract', 'summary', 'overview', 'contents', 'index'],
            'cjk': ['タイトル', '題目', '標題', '章', '部', '節', '概要', 
                   '要約', '目次', '索引', '标题', '章节', '摘要']
        }
        
        # Words that are unlikely to be headings
        self.exclude_keywords = [
            'page', 'figure', 'table', 'appendix', 'reference', 'bibliography',
            'footnote', 'header', 'footer', 'copyright', 'rights', 'reserved'
        ]
    
    def analyze_document_structure(self, pages_data: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Main method to analyze document and extract structured outline
        """
        if not pages_data:
            return []
        
        # Step 1: Analyze font distribution
        from pdf_extractor import AdvancedPDFExtractor
        extractor = AdvancedPDFExtractor()
        font_analysis = extractor.analyze_font_distribution(pages_data)
        self.font_hierarchy = font_analysis['hierarchy']
        
        # Step 2: Find all potential headings
        potential_headings = self._find_potential_headings(pages_data)
        
        # Step 3: Classify headings with confidence scores
        classified_headings = self._classify_headings(potential_headings)
        
        # Step 4: Post-process and clean results
        final_outline = self._post_process_outline(classified_headings)
        
        return final_outline
    
    def _find_potential_headings(self, pages_data: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Find all elements that could potentially be headings"""
        potential_headings = []
        
        for page_elements in pages_data:
            for element in page_elements:
                confidence = self._calculate_heading_confidence(element)
                
                if confidence >= self.min_confidence:
                    heading_info = element.copy()
                    heading_info['confidence'] = confidence
                    potential_headings.append(heading_info)
        
        # Sort by confidence and position
        potential_headings.sort(key=lambda x: (x['page'], -x['confidence'], x['y_pos']))
        
        return potential_headings
    
    def _calculate_heading_confidence(self, element: Dict[str, Any]) -> float:
        """Calculate confidence score for element being a heading"""
        confidence = 0.0
        text = element['text']
        
        # Font size factor (30% weight)
        size_score = self._calculate_size_score(element['size'])
        confidence += size_score * 0.3
        
        # Bold formatting (15% weight)
        if element.get('is_bold', False):
            confidence += 0.15
        
        # Position analysis (20% weight)
        position_score = self._calculate_position_score(element)
        confidence += position_score * 0.2
        
        # Pattern matching (20% weight) 
        pattern_score = self._calculate_pattern_score(text, element.get('language_type', 'latin'))
        confidence += pattern_score * 0.2
        
        # Length analysis (10% weight)
        length_score = self._calculate_length_score(text)
        confidence += length_score * 0.1
        
        # Special bonuses/penalties (5% weight)
        special_score = self._calculate_special_score(element)
        confidence += special_score * 0.05
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _calculate_size_score(self, font_size: float) -> float:
        """Calculate score based on font size relative to document hierarchy"""
        if not hasattr(self, 'font_hierarchy') or not self.font_hierarchy:
            # Fallback scoring
            if font_size >= 16: return 1.0
            elif font_size >= 14: return 0.8
            elif font_size >= 12: return 0.6
            else: return 0.3
        
        title_size = self.font_hierarchy.get('title', 16)
        h1_size = self.font_hierarchy.get('H1', 14)
        
        if font_size >= title_size:
            return 1.0
        elif font_size >= h1_size:
            return 0.8
        elif font_size >= self.font_hierarchy.get('H2', 12):
            return 0.6
        elif font_size >= self.font_hierarchy.get('H3', 10):
            return 0.4
        else:
            return 0.2
    
    def _calculate_position_score(self, element: Dict[str, Any]) -> float:
        """Calculate score based on element position"""
        score = 0.0
        
        # Left alignment bonus
        if element.get('is_left_aligned', False):
            score += 0.4
        
        # Center alignment bonus (for titles)
        if element.get('is_centered', False):
            score += 0.3
        
        # Top of page bonus
        if element['y_pos'] < 150:  # Near top of page
            score += 0.3
        
        return score
    
    def _calculate_pattern_score(self, text: str, language_type: str) -> float:
        """Calculate score based on text patterns"""
        text_clean = text.strip()
        
        # Check standard patterns
        for pattern in self.heading_patterns:
            if re.match(pattern, text_clean):
                return 0.8
        
        # Check CJK patterns
        if language_type in ['japanese', 'chinese', 'cjk']:
            for pattern in self.cjk_patterns:
                if re.match(pattern, text_clean):
                    return 0.8
        
        # Check for title keywords
        text_lower = text_clean.lower()
        keywords = self.title_keywords.get(language_type, self.title_keywords['latin'])
        
        for keyword in keywords:
            if keyword in text_lower:
                return 0.6
        
        # Check for uppercase (potential heading)
        if text_clean.isupper() and len(text_clean) > 2:
            return 0.4
        
        # Check if starts with capital and has few words
        if (text_clean[0].isupper() and 
            len(text_clean.split()) <= 8 and 
            not text_clean.endswith('.')):
            return 0.3
        
        return 0.0
    
    def _calculate_length_score(self, text: str) -> float:
        """Calculate score based on text length (headings are usually concise)"""
        char_count = len(text)
        word_count = len(text.split())
        
        # Optimal length for headings
        if 5 <= char_count <= 50 and 1 <= word_count <= 8:
            return 1.0
        elif 3 <= char_count <= 100 and 1 <= word_count <= 12:
            return 0.7
        elif char_count <= 150:
            return 0.4
        else:
            return 0.1
    
    def _calculate_special_score(self, element: Dict[str, Any]) -> float:
        """Calculate special bonuses and penalties"""
        text = element['text'].lower()
        score = 0.0
        
        # Penalty for excluded keywords
        for keyword in self.exclude_keywords:
            if keyword in text:
                score -= 0.5
                break
        
        # Bonus for numeric indicators
        if element.get('starts_with_number', False):
            score += 0.3
        
        # Bonus for being on early pages (more likely to be important)
        if element['page'] <= 3:
            score += 0.2
        
        # Penalty for very late pages (less likely to be main headings)
        if element['page'] > 20:
            score -= 0.1
        
        return score
    
    def _classify_headings(self, potential_headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify headings into title, H1, H2, H3 categories"""
        classified = []
        title_found = False
        
        for heading in potential_headings:
            level = self._classify_heading_level(heading, title_found)
            
            if level:
                heading_result = {
                    'level': level,
                    'text': heading['text'],
                    'page': heading['page'],
                    'confidence': heading['confidence'],
                    'font_size': heading['size']
                }
                classified.append(heading_result)
                
                if level == 'title':
                    title_found = True
        
        return classified
    
    def _classify_heading_level(self, heading: Dict[str, Any], title_found: bool) -> Optional[str]:
        """Classify individual heading level"""
        confidence = heading['confidence']
        font_size = heading['size']
        page = heading['page']
        text = heading['text']
        
        # Title detection (only one title, prefer early pages)
        if (not title_found and 
            page <= 2 and 
            confidence >= self.title_confidence and
            font_size >= self.font_hierarchy.get('title', 16) - 1):
            
            # Additional title checks
            if (len(text.split()) <= 10 and 
                not any(exclude in text.lower() for exclude in self.exclude_keywords)):
                return 'title'
        
        # H1, H2, H3 classification based on font size
        if font_size >= self.font_hierarchy.get('H1', 14) - 0.5:
            return 'H1'
        elif font_size >= self.font_hierarchy.get('H2', 12) - 0.5:
            return 'H2'
        elif font_size >= self.font_hierarchy.get('H3', 10) - 0.5:
            return 'H3'
        
        # Pattern-based classification for edge cases
        if re.match(r'^\d+\.?\s+', text):
            return 'H1'
        elif re.match(r'^\d+\.\d+\.?\s+', text):
            return 'H2'
        elif re.match(r'^\d+\.\d+\.\d+\.?\s+', text):
            return 'H3'
        
        return None
    
    def _post_process_outline(self, classified_headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process and clean the final outline"""
        if not classified_headings:
            return []
        
        # Separate title from outline
        title_headings = [h for h in classified_headings if h['level'] == 'title']
        outline_headings = [h for h in classified_headings if h['level'] != 'title']
        
        # Remove duplicates and clean text
        seen_texts = set()
        clean_outline = []
        
        for heading in outline_headings:
            text_clean = self._clean_heading_text(heading['text'])
            
            # Skip if we've seen this text before or it's too generic
            if text_clean.lower() not in seen_texts and len(text_clean) > 2:
                seen_texts.add(text_clean.lower())
                
                clean_heading = {
                    'level': heading['level'],
                    'text': text_clean,
                    'page': heading['page']
                }
                clean_outline.append(clean_heading)
        
        # Sort by page number and logical order
        clean_outline.sort(key=lambda x: (x['page'], self._get_level_priority(x['level'])))
        
        return clean_outline
    
    def _clean_heading_text(self, text: str) -> str:
        """Clean heading text for final output"""
        # Remove leading numbers and punctuation
        text = re.sub(r'^[\d\.\s\-\)\(]+', '', text)
        
        # Remove trailing punctuation except meaningful ones
        text = re.sub(r'[^\w\s\.\!\?]+$', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Title case for better presentation
        if text.islower() or text.isupper():
            text = text.title()
        
        return text
    
    def _get_level_priority(self, level: str) -> int:
        """Get priority for sorting (lower number = higher priority)"""
        priorities = {'H1': 1, 'H2': 2, 'H3': 3}
        return priorities.get(level, 4)
    
    def find_document_title(self, pages_data: List[List[Dict[str, Any]]]) -> str:
        """Find the most likely document title"""
        if not pages_data:
            return "Untitled Document"
        
        # Look in first 2 pages
        title_candidates = []
        
        for page_num in range(min(2, len(pages_data))):
            for element in pages_data[page_num]:
                confidence = self._calculate_heading_confidence(element)
                
                if (confidence >= self.title_confidence and 
                    element['size'] >= self.font_hierarchy.get('title', 16) - 2):
                    
                    title_candidates.append({
                        'text': element['text'],
                        'confidence': confidence,
                        'size': element['size'],
                        'page': element['page']
                    })
        
        if title_candidates:
            # Sort by confidence and size
            title_candidates.sort(key=lambda x: (x['confidence'], x['size']), reverse=True)
            return self._clean_heading_text(title_candidates[0]['text'])
        
        # Fallback: largest text on first page
        if pages_data and pages_data[0]:
            largest_element = max(pages_data[0], key=lambda x: x['size'])
            return self._clean_heading_text(largest_element['text'])
        
        return "Untitled Document"