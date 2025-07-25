# Create the corrected local test script
import os
import sys
from pathlib import Path
from pdf_extractor import AdvancedPDFExtractor
from heading_detector import SmartHeadingDetector
from process_pdfs import PDFProcessor
import json

def test_local():
    input_dir = Path("input")
    output_dir = Path("output")
    
    # Create directories if they don't exist
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in input/ directory")
        print("Please add a test PDF file to input/ directory")
        print("\nExample commands to add a test PDF:")
        print("  cp /path/to/your/document.pdf input/")
        print("  mv sample.pdf input/")
        return False
    
    print(f"✅ Found {len(pdf_files)} PDF files")
    
    # Initialize the PDFProcessor (this will create extractor and detector internally)
    processor = PDFProcessor()
    
    for pdf_file in pdf_files:
        print(f"\n🔄 Processing: {pdf_file.name}")
        
        try:
            # Use the PDFProcessor's process_single_pdf method
            result = processor.process_single_pdf(pdf_file)
            
            print(f"📄 Title: {result['title']}")
            print(f"📝 Outline entries: {len(result['outline'])}")
            
            # Show first few outline entries if available
            if result['outline']:
                print("📋 Sample outline entries:")
                for i, entry in enumerate(result['outline'][:3]):
                    level = entry.get('level', 'Unknown')
                    text = entry.get('text', 'No text')[:60]
                    page = entry.get('page', 'Unknown')
                    print(f"   {i+1}. [{level}] {text}... (Page {page})")
            
            # Save result for inspection
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error processing {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Local testing completed!")
    print(f"📁 Check output files in: {output_dir.absolute()}")
    return True

def test_processor_components():
    """Test individual components"""
    print("🔧 Testing PDFProcessor components...")
    
    try:
        processor = PDFProcessor()
        print("  ✅ PDFProcessor initialized successfully")
        print(f"  ✅ Extractor type: {type(processor.extractor).__name__}")
        print(f"  ✅ Detector type: {type(processor.detector).__name__}")
        print(f"  ✅ Processed count: {processor.processed_count}")
        print(f"  ✅ Total processing time: {processor.total_processing_time}")
        return True
    except Exception as e:
        print(f"  ❌ Component test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 LOCAL PDF PROCESSING TEST")
    print("=" * 60)
    
    # Test components first
    if not test_processor_components():
        print("Component test failed. Exiting.")
        sys.exit(1)
    
    print()
    
    # Test PDF processing
    success = test_local()
    
    if success:
        print("\n🚀 Ready for Docker testing!")
        print("Next step: docker build --platform linux/amd64 -t pdf-extractor .")
    else:
        print("\n⚠️  Add a test PDF file to input/ directory and run again")
    
    sys.exit(0 if success else 1)

