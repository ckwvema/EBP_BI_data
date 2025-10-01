#!/usr/bin/env python3
"""
Example script showing how to use the EBP data ingestion script.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Example usage of the EBP data ingestion script."""
    print("EBP Data Ingestion - Example Usage")
    print("=" * 40)
    
    # Import the main function
    from ingest_ebp_data import main as ingest_main
    
    try:
        print("Starting EBP data ingestion...")
        print("This will:")
        print("1. Connect to EBP API")
        print("2. Fetch all data from various endpoints")
        print("3. Transform and clean the data")
        print("4. Export to CSV files")
        print("\nPress Ctrl+C to cancel...")
        
        # Run the main ingestion process
        ingest_main()
        
        print("\n✅ Data ingestion completed successfully!")
        print("Check the export directory for the generated CSV files.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during data ingestion: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

