#!/usr/bin/env python3
"""
Test script for the improved title chain extraction.
"""

import sys
import os
from datetime import datetime

# Add the path to import the fixed title_chain module
sys.path.insert(0, '.')

try:
    from gistax.desoto.services.title_chain import (
        ChainEntry, 
        parse_table_data, 
        parse_date, 
        is_vesting_deed, 
        get_24_month_chain,
        process_title_document
    )
    print("✓ Successfully imported title_chain module")
except ImportError as e:
    print(f"✗ Failed to import title_chain module: {e}")
    sys.exit(1)

def test_parse_date():
    """Test date parsing functionality."""
    print("\n=== Testing Date Parsing ===")
    
    test_dates = [
        "10/17/2024",
        "11/18/2021", 
        "1/5/2023",
        "12-25-2022",
        "2024-03-15",
        "invalid",
        ""
    ]
    
    for date_str in test_dates:
        result = parse_date(date_str)
        if result:
            print(f"✓ '{date_str}' -> {result.strftime('%Y-%m-%d')}")
        else:
            print(f"✗ '{date_str}' -> None")

def test_is_vesting_deed():
    """Test vesting deed detection."""
    print("\n=== Testing Vesting Deed Detection ===")
    
    test_instruments = [
        ("WARRANTY DEED", True),
        ("DEED OF TRUST", False),
        ("QUITCLAIM DEED", True),
        ("MORTGAGE", False),
        ("SPECIAL WARRANTY DEED", True),
        ("UCC FINANCING STATEMENT", False),
        ("DEED", True),
        ("ASSIGNMENT OF LEASES", False)
    ]
    
    for instrument, expected in test_instruments:
        result = is_vesting_deed(instrument)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{instrument}' -> {result} (expected: {expected})")

def test_parse_table_data():
    """Test table data parsing with sample data."""
    print("\n=== Testing Table Data Parsing ===")
    
    # Sample table data matching the user's example
    sample_table = [
        ["GRANTOR:", "GRANTEE:", "INSTRUMENT", "DATED:", "RECORDING:"],
        ["SOUTH", "CHERRY TREE DEVELOPMENT, INC LEGACY NEW HOMES,", "LLC WARRANTY DEED", "10/17/2024", "1024-18978"],
        ["SHORT", "CREEK INVESTMENTS, LLC SOUTH CHERRY TREE DEVELOPMENT,", "INC WARRANTY DEED", "11/18/2021", "979-60"]
    ]
    
    entries = parse_table_data(sample_table)
    
    print(f"Found {len(entries)} entries:")
    for i, entry in enumerate(entries, 1):
        print(f"\nEntry {i}:")
        print(f"  Date: {entry.date_string}")
        print(f"  Grantor: {entry.grantor}")
        print(f"  Grantee: {entry.grantee}")
        print(f"  Instrument: {entry.instrument}")
        print(f"  Recording: {entry.book_page}")
        print(f"  Is Vesting: {entry.is_vesting}")

def test_get_24_month_chain():
    """Test 24-month chain filtering."""
    print("\n=== Testing 24-Month Chain ===")
    
    # Create sample entries
    sample_entries = [
        ChainEntry(
            date=datetime(2024, 10, 17),
            date_string="10/17/2024",
            grantor="SOUTH",
            grantee="CHERRY TREE DEVELOPMENT",
            instrument="WARRANTY DEED",
            book_page="1024-18978",
            is_vesting=True
        ),
        ChainEntry(
            date=datetime(2021, 11, 18),
            date_string="11/18/2021",
            grantor="SHORT",
            grantee="CREEK INVESTMENTS",
            instrument="WARRANTY DEED", 
            book_page="979-60",
            is_vesting=True
        ),
        ChainEntry(
            date=datetime(2023, 5, 15),
            date_string="05/15/2023",
            grantor="TEST GRANTOR",
            grantee="TEST GRANTEE",
            instrument="DEED OF TRUST",
            book_page="800-123",
            is_vesting=False
        )
    ]
    
    # Test with current date
    chain_deeds = get_24_month_chain(sample_entries, datetime(2024, 12, 1))
    
    print(f"24-month chain contains {len(chain_deeds)} vesting deeds:")
    for deed in chain_deeds:
        print(f"  {deed.date_string}: {deed.grantor} -> {deed.grantee} ({deed.instrument})")

def main():
    """Run all tests."""
    print("Title Chain Extraction - Test Suite")
    print("=" * 50)
    
    try:
        test_parse_date()
        test_is_vesting_deed()
        test_parse_table_data()
        test_get_24_month_chain()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()