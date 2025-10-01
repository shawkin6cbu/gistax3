# gistax3

Title document processor for DeSoto County real estate transactions. Scrapes public records, calculates property taxes, extracts chain of title from PDFs, and generates lender-ready documents.

## What it does

Built this to automate title document processing at work. Takes a title search PDF, pulls out the relevant vesting deeds from the past 24 months, grabs tax info, and merges everything into a formatted Word doc. Also handles parcel lookups and tax calculations for DeSoto County properties. Reduced my work time from 20 minutes to just a few seconds. 

## Features

**Parcel Lookup** - Searches DeSoto County GIS for property info by address. Auto-completes as you type, pulls owner names, parcel numbers, legal descriptions.

**Tax Calculator** - Hits the DeSoto County tax estimator directly. Input the appraised value, get the 2025 estimated taxes broken down by district.

**Chain of Title Extraction** - Drag and drop a title search PDF. Uses pdfplumber to extract tables, falls back to regex parsing if needed. Identifies vesting deeds (warranty deeds, quitclaim deeds, executor/executrix deeds, etc.) vs non-vesting instruments (deeds of trust, mortgages, liens, judgements, etc). Automatically selects the minimum set of deeds covering the past 24 months.

**Document Generation** - Takes all the extracted data and fills a Word template with property info, owner details, tax amounts, and the filtered chain of title. 

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

The GUI has three tabs - start with Parcel Finder to look up a property, then drop your title search PDF in the Processing tab.

## Tech

- **GUI**: ttkbootstrap (dark theme tkinter)
- **PDF Processing**: pdfplumber for table extraction, PyPDF2 fallback
- **Web Scraping**: requests + BeautifulSoup for tax data
- **GIS API**: DeSoto County ArcGIS REST services
- **Document Generation**: python-docx with custom templates

## How the Chain Logic Works

The tricky part was getting the 24-month vesting deed chain right. Here's the logic:

1. Parse all entries from the title search
2. Filter for vesting deeds only (warranty deeds, quitclaim deeds)
3. Sort by date, newest first
4. Include deeds going back until the oldest one is ≥24 months old
5. If the newest deed is already 24+ months old, just return that one

Quick and Easy table generation and data extraction

## File Structure

```
main.py                     # Entry point
desoto/
├── app.py                  # Main app window
├── data.py                 # Shared data between tabs
├── gui/
│   ├── parcel_tab.py      # Parcel search interface
│   ├── tax_tab.py         # Tax calculator
│   └── processing_tab.py  # Document processor
└── services/
    ├── parcels.py         # DeSoto County GIS API
    ├── tax.py             # Tax scraper
    ├── title_chain.py     # Chain extraction logic
    ├── tax_document.py    # Tax info parser
    └── document_splitter.py # PDF splitter/classifier
templates/
└── td_tmplt2.docx         # Output document template
```

## Notes

Built specifically for DeSoto County, Mississippi. The parcel API and tax calculator are hardcoded to their systems. Could adapt for other counties by updating the endpoints in `services/parcels.py` and `services/tax.py`.

The PDF parsing is tuned for the specific format of title searches we use. tweak the regex patterns in `title_chain.py` to adapt to other title company's formatting if needed.

Default template expects specific placeholder names - modify `td_tmplt2.docx` to customize the output format.
