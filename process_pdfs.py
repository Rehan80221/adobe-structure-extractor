#!/usr/bin/env python3
"""
Adobe Hackathon 2025 - Challenge 1A: PDF Structure Extractor
Main processing script with optimized performance and multilingual support
"""
import os
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import our custom modules
from pdf_extractor import AdvancedPDFExtractor
from heading_detector import SmartHeadingDetector

class PDFProcessor:
    def __init__(self):
        self.extractor = AdvancedPDFExtractor()
        self.detector = SmartHeadingDetector()
        self.processed_count = 0
        self.total_processing_time = 0.0
        
    def process_single_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process a single PDF file and extract structured outline
        """
        start_time = time.time()
        
        try:
            print(f"Processing: {pdf_path.name}")
            
            # Step 1: Extract text with metadata
            pages_data = self.extractor.extract_with_metadata(str(pdf_path))
            
            if not pages_data:
                print(f"Warning: No data extracted from {pdf_path.name}")
                return self._create_empty_result()
            
            # Step 2: Detect headings and structure
            outline_data = self.detector.analyze_document_structure(pages_data)
            
            # Step 3: Find document title
            title = self.detector.find_document_title(pages_data)
            
            # Step 4: Build final structure
            result = {
                "title": title,
                "outline": outline_data
            }
            
            # Step 5: Validate result format
            validated_result = self._validate_and_clean_result(result)
            
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            print(f"Completed: {pdf_path.name} (Title: '{title}', Headings: {len(outline_data)}, Time: {processing_time:.2f}s)")
            
            return validated_result
            
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_empty_result()
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result structure for failed processing"""
        return {
            "title": "Untitled Document",
            "outline": []
        }
    
    def _validate_and_clean_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the result to match expected schema"""
        # Ensure title is a string
        if not isinstance(result.get("title"), str):
            result["title"] = "Untitled Document"
        
        # Ensure outline is a list
        if not isinstance(result.get("outline"), list):
            result["outline"] = []
        
        # Validate each outline item
        clean_outline = []
        for item in result["outline"]:
            if isinstance(item, dict) and all(key in item for key in ["level", "text", "page"]):
                # Ensure correct types
                clean_item = {
                    "level": str(item["level"]),
                    "text": str(item["text"]).strip(),
                    "page": int(item["page"])
                }
                
                # Validate level values
                if clean_item["level"] in ["H1", "H2", "H3"] and len(clean_item["text"]) > 0:
                    clean_outline.append(clean_item)
        
        result["outline"] = clean_outline
        return result
    
    def process_all_pdfs(self, input_dir: Path, output_dir: Path) -> bool:
        """
        Process all PDF files in the input directory
        """
        try:
            # Ensure input directory exists
            if not input_dir.exists():
                print(f"Error: Input directory {input_dir} does not exist")
                return False
            
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Find all PDF files
            pdf_files = list(input_dir.glob("*.pdf"))
            
            if not pdf_files:
                print("No PDF files found in input directory")
                return True
            
            print(f"Found {len(pdf_files)} PDF files to process")
            
            # Process each PDF
            success_count = 0
            for pdf_file in pdf_files:
                try:
                    # Process PDF
                    result = self.process_single_pdf(pdf_file)
                    
                    # Save output JSON
                    output_file = output_dir / f"{pdf_file.stem}.json"
                    self._save_json_result(result, output_file)
                    
                    success_count += 1
                    self.processed_count += 1
                    
                except Exception as e:
                    print(f"Failed to process {pdf_file.name}: {e}")
                    continue
            
            # Print summary
            print(f"\nProcessing Summary:")
            print(f"Total files: {len(pdf_files)}")
            print(f"Successfully processed: {success_count}")
            print(f"Failed: {len(pdf_files) - success_count}")
            print(f"Average processing time: {self.total_processing_time / max(success_count, 1):.2f}s per file")
            
            return success_count > 0
            
        except Exception as e:
            print(f"Error in batch processing: {e}")
            return False
    
    def _save_json_result(self, result: Dict[str, Any], output_file: Path):
        """Save result to JSON file with proper formatting"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Saved: {output_file.name}")
            
        except Exception as e:
            print(f"Error saving {output_file}: {e}")
            raise

def validate_environment():
    """Validate that the environment is set up correctly"""
    required_dirs = ["/app/input", "/app/output"]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            print(f"Warning: {dir_path} does not exist, creating...")
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Error creating {dir_path}: {e}")
                return False
    
    # Check if input directory is readable
    input_path = Path("/app/input")
    if not os.access(input_path, os.R_OK):
        print(f"Error: Cannot read from {input_path}")
        return False
    
    # Check if output directory is writable
    output_path = Path("/app/output")
    if not os.access(output_path, os.W_OK):
        print(f"Error: Cannot write to {output_path}")
        return False
    
    return True

def main():
    """Main entry point"""
    print("Adobe Hackathon 2025 - Challenge 1A: PDF Structure Extractor")
    print("=" * 60)
    
    # Validate environment
    if not validate_environment():
        print("Environment validation failed!")
        sys.exit(1)
    
    # Set up paths
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Initialize processor
    processor = PDFProcessor()
    
    # Start processing
    start_time = time.time()
    
    try:
        success = processor.process_all_pdfs(input_dir, output_dir)
        
        total_time = time.time() - start_time
        print(f"\nTotal execution time: {total_time:.2f} seconds")
        
        if success:
            print("Processing completed successfully!")
            sys.exit(0)
        else:
            print("Processing failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()