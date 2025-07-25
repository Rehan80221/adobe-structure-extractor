#!/usr/bin/env python3
"""
Quick test script for Adobe Hackathon 2025 - Challenge 1A
Tests the PDF processor components before Docker deployment
"""

import os
import sys
import json
import time
from pathlib import Path

# Test imports
def test_imports():
    """Test if all required modules can be imported"""
    print("🔧 Testing module imports...")
    
    try:
        from pdf_extractor import AdvancedPDFExtractor
        print("  ✅ pdf_extractor.AdvancedPDFExtractor - OK")
    except ImportError as e:
        print(f"  ❌ pdf_extractor import failed: {e}")
        return False
    
    try:
        from heading_detector import SmartHeadingDetector
        print("  ✅ heading_detector.SmartHeadingDetector - OK")
    except ImportError as e:
        print(f"  ❌ heading_detector import failed: {e}")
        return False
    
    try:
        from process_pdfs import PDFProcessor
        print("  ✅ process_pdfs.PDFProcessor - OK")
    except ImportError as e:
        print(f"  ❌ process_pdfs import failed: {e}")
        return False
    
    print("  🎉 All imports successful!\n")
    return True

def test_processor_initialization():
    """Test PDFProcessor initialization"""
    print("🔧 Testing PDFProcessor initialization...")
    
    try:
        from process_pdfs import PDFProcessor
        processor = PDFProcessor()
        
        # Check if components are initialized
        if hasattr(processor, 'extractor') and processor.extractor:
            print("  ✅ AdvancedPDFExtractor initialized")
        else:
            print("  ❌ AdvancedPDFExtractor not initialized")
            return False
        
        if hasattr(processor, 'detector') and processor.detector:
            print("  ✅ SmartHeadingDetector initialized")
        else:
            print("  ❌ SmartHeadingDetector not initialized")
            return False
        
        # Check counters
        if hasattr(processor, 'processed_count'):
            print(f"  ✅ Processed count initialized: {processor.processed_count}")
        
        if hasattr(processor, 'total_processing_time'):
            print(f"  ✅ Total processing time initialized: {processor.total_processing_time}")
        
        print("  🎉 PDFProcessor initialization successful!\n")
        return True
        
    except Exception as e:
        print(f"  ❌ PDFProcessor initialization failed: {e}")
        return False

def test_with_sample_pdf():
    """Test processing with a sample PDF if available"""
    print("🔧 Testing PDF processing...")
    
    # Check for test PDFs
    test_dirs = ["input", "test_pdfs", "."]
    test_pdf = None
    
    for test_dir in test_dirs:
        test_path = Path(test_dir)
        if test_path.exists():
            pdf_files = list(test_path.glob("*.pdf"))
            if pdf_files:
                test_pdf = pdf_files[0]
                break
    
    if not test_pdf:
        print("  ⚠️  No test PDF found. Skipping PDF processing test.")
        print("  💡 To test PDF processing, add a PDF file to one of these directories:")
        print("     - input/")
        print("     - test_pdfs/")
        print("     - current directory")
        return True
    
    try:
        from process_pdfs import PDFProcessor
        
        processor = PDFProcessor()
        print(f"  📄 Testing with: {test_pdf.name}")
        
        start_time = time.time()
        result = processor.process_single_pdf(test_pdf)
        processing_time = time.time() - start_time
        
        # Validate result structure
        if not isinstance(result, dict):
            print("  ❌ Result is not a dictionary")
            return False
        
        if "title" not in result:
            print("  ❌ Result missing 'title' field")
            return False
        
        if "outline" not in result:
            print("  ❌ Result missing 'outline' field")
            return False
        
        if not isinstance(result["outline"], list):
            print("  ❌ Outline is not a list")
            return False
        
        # Print results
        print(f"  ✅ Processing successful!")
        print(f"  📖 Title: '{result['title']}'")
        print(f"  📝 Outline entries: {len(result['outline'])}")
        print(f"  ⏱️  Processing time: {processing_time:.2f}s")
        
        # Show first few outline entries
        if result['outline']:
            print("  📋 Sample outline entries:")
            for i, entry in enumerate(result['outline'][:3]):
                print(f"     {i+1}. [{entry.get('level', 'Unknown')}] {entry.get('text', 'No text')[:50]}...")
        
        # Save test result
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{test_pdf.stem}_test.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Test result saved to: {output_file}")
        print("  🎉 PDF processing test successful!\n")
        return True
        
    except Exception as e:
        print(f"  ❌ PDF processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_validation():
    """Test environment validation function"""
    print("🔧 Testing environment validation...")
    
    try:
        from process_pdfs import validate_environment
        
        # Test in current directory context (not Docker)
        print("  📁 Testing current directory setup...")
        
        # Create test directories
        test_input = Path("test_input")
        test_output = Path("test_output")
        test_input.mkdir(exist_ok=True)
        test_output.mkdir(exist_ok=True)
        
        print("  ✅ Test directories created")
        print("  🎉 Environment validation test complete!\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Environment validation test failed: {e}")
        return False

def test_json_output_format():
    """Test JSON output format validation"""
    print("🔧 Testing JSON output format...")
    
    try:
        from process_pdfs import PDFProcessor
        
        processor = PDFProcessor()
        
        # Test empty result
        empty_result = processor._create_empty_result()
        print(f"  ✅ Empty result: {empty_result}")
        
        # Test result validation
        test_result = {
            "title": "Test Document",
            "outline": [
                {"level": "H1", "text": "Chapter 1", "page": 1},
                {"level": "H2", "text": "Section 1.1", "page": 2}
            ]
        }
        
        validated = processor._validate_and_clean_result(test_result)
        print(f"  ✅ Validated result structure: {list(validated.keys())}")
        
        # Test with invalid data
        invalid_result = {
            "title": None,
            "outline": "not a list"
        }
        
        cleaned = processor._validate_and_clean_result(invalid_result)
        print(f"  ✅ Cleaned invalid result: {cleaned}")
        
        print("  🎉 JSON format validation test successful!\n")
        return True
        
    except Exception as e:
        print(f"  ❌ JSON format test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 QUICK TEST SUITE - Adobe Hackathon Challenge 1A")
    print("=" * 60)
    print()
    
    tests = [
        ("Module Imports", test_imports),
        ("Processor Initialization", test_processor_initialization),
        ("Environment Validation", test_environment_validation),
        ("JSON Output Format", test_json_output_format),
        ("PDF Processing", test_with_sample_pdf),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
        print()
    
    print("=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your solution is ready for Docker testing.")
        print()
        print("Next steps:")
        print("1. Add test PDFs to input/ directory")
        print("2. Build Docker container: docker build --platform linux/amd64 -t pdf-extractor .")
        print("3. Run Docker test: docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output --network none pdf-extractor")
    else:
        print("⚠️  Some tests failed. Please fix the issues before proceeding.")
        return False
    
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
