import re
import io
import PyPDF2
from typing import Tuple, List

# OPTIMIZATION 1: Pre-compiled regex patterns
CHAIN_INDICATORS_PATTERN = re.compile(
    r'CHAIN OF TITLE|FILED GRANTOR GRANTEE INSTRUMENT|'
    r'GRANTOR GRANTEE INSTRUMENT BOOK-PAGE|WARRANTY DEED|'
    r'DEED OF TRUST|TRUSTEE\'S DEED', re.IGNORECASE
)

TAX_INDICATORS_PATTERN = re.compile(
    r'TAX INFORMATION|TAX YEAR|ASSESSMENT|MILLAGE RATE|'
    r'HOMESTEAD CREDIT|TAXES PAID IN FULL|TAX COLLECTOR|'
    r'COUNTY SCHOOL TAX', re.IGNORECASE
)

def identify_page_type(text: str) -> str:
    """
    Identify whether a page contains chain of title or tax information.
    Returns: 'chain', 'tax', or 'other'
    """
    # Use pre-compiled regex for faster counting
    chain_score = len(CHAIN_INDICATORS_PATTERN.findall(text))
    tax_score = len(TAX_INDICATORS_PATTERN.findall(text))
    
    # Strong indicators get extra weight
    if 'CHAIN OF TITLE' in text.upper():
        chain_score += 3
    if 'TAX INFORMATION' in text.upper():
        tax_score += 3
    
    if chain_score > tax_score and chain_score >= 2:
        return 'chain'
    elif tax_score > chain_score and tax_score >= 2:
        return 'tax'
    else:
        return 'other'

def extract_pages_by_type(pdf_path: str) -> Tuple[bytes, bytes, str]:
    """
    Extracts chain of title and tax pages from a PDF in a single pass,
    reading the file from disk only once to maximize speed.
    
    Returns:
        Tuple of (chain_pdf_bytes, tax_pdf_bytes, status_message)
    """
    chain_writer = PyPDF2.PdfWriter()
    tax_writer = PyPDF2.PdfWriter()
    
    try:
        # --- SINGLE READ OPTIMIZATION ---
        # Read the PDF from disk only ONCE. Both text extraction for classification
        # and page manipulation will happen in this single pass.
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                # 1. Extract text for classification
                text = page.extract_text() or ""
                page_type = identify_page_type(text)
                
                # 2. Add the page object directly to the appropriate writer
                if page_type == 'chain':
                    chain_writer.add_page(page)
                elif page_type == 'tax':
                    tax_writer.add_page(page)

        # --- Create in-memory PDFs from the writers ---
        chain_pdf_bytes = b''
        if len(chain_writer.pages) > 0:
            with io.BytesIO() as stream:
                chain_writer.write(stream)
                chain_pdf_bytes = stream.getvalue()

        tax_pdf_bytes = b''
        if len(tax_writer.pages) > 0:
            with io.BytesIO() as stream:
                tax_writer.write(stream)
                tax_pdf_bytes = stream.getvalue()
        
        # --- Generate status message ---
        status_parts = []
        if len(chain_writer.pages) > 0:
            status_parts.append(f"Found {len(chain_writer.pages)} chain page(s)")
        if len(tax_writer.pages) > 0:
            status_parts.append(f"Found {len(tax_writer.pages)} tax page(s)")
        if not status_parts:
            status_parts.append("No chain or tax pages identified")
        
        status = ". ".join(status_parts)
        
        return chain_pdf_bytes, tax_pdf_bytes, status
        
    except Exception as e:
        # Improve error reporting for common issues like encrypted PDFs
        if "read" in str(e) and "is encrypted" in str(e):
             return b'', b'', "Error: PDF is encrypted and cannot be read."
        return b'', b'', f"Error processing PDF: {str(e)}"

def process_comprehensive_document(pdf_path: str) -> Tuple[bool, str, dict]:
    """
    Process a comprehensive title search document and extract all relevant information.
    This version is optimized to pass data in-memory and read the source PDF only once.
    """
    from desoto.services.title_chain import process_title_document
    from desoto.services.tax_document import process_tax_document
    
    results = {
        'chain_entries': [],
        'all_entries': [],
        'tax_total': None,
        'tax_date_paid': None,
        'status': ''
    }
    
    try:
        # This function now performs the file read and split in a single, optimized pass.
        chain_bytes, tax_bytes, extract_status = extract_pages_by_type(pdf_path)
        results['status'] = extract_status
        
        # Process chain document (from in-memory bytes)
        if chain_bytes:
            success, msg, chain_deeds, all_entries = process_title_document(file_bytes=chain_bytes)
            if success:
                results['chain_entries'] = chain_deeds
                results['all_entries'] = all_entries
            else:
                results['status'] += f". Chain processing: {msg}"
        
        # Process tax document (from in-memory bytes)
        if tax_bytes:
            success, msg, total_amount, date_paid = process_tax_document(file_bytes=tax_bytes)
            if success:
                results['tax_total'] = total_amount
                results['tax_date_paid'] = date_paid
            else:
                results['status'] += f". Tax processing: {msg}"
        
        # Determine overall success
        overall_success = bool(results['chain_entries'] or results['tax_total'])
        
        if overall_success:
            msg = f"Successfully processed document. {results['status']}"
        else:
            msg = f"No data extracted. {results['status']}"
        
        return overall_success, msg, results
        
    except Exception as e:
        return False, f"Error processing document: {str(e)}", results