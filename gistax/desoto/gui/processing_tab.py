import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES
from desoto.services.title_chain import (
    extract_text_from_pdf, 
    parse_chain_text, 
    get_24_month_chain,
    process_title_document
)
import threading
import os
from docx import Document

class ProcessingTab(ttk.Frame):
    def __init__(self, parent, shared_data):
        super().__init__(parent, padding=10)
        self.shared_data = shared_data

        # Main layout frames
        left_frame = ttk.Frame(self)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        right_frame = ttk.Frame(self)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # --- Property Information ---
        prop_frame = ttk.LabelFrame(left_frame, text="Property Information", padding=10)
        prop_frame.pack(fill="x", pady=(0, 10))
        self.pin_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.owner_var = tk.StringVar()
        self.city_var = tk.StringVar()
        self.legal_desc_var = tk.StringVar()
        self._create_entry_row(prop_frame, "PIN:", self.pin_var, 0)
        self._create_entry_row(prop_frame, "Address:", self.address_var, 1)
        self._create_entry_row(prop_frame, "Owner:", self.owner_var, 2)
        self._create_entry_row(prop_frame, "City/State/ZIP:", self.city_var, 3)
        self._create_entry_row(prop_frame, "Legal Desc:", self.legal_desc_var, 4)

        # --- Tax Information ---
        tax_frame = ttk.LabelFrame(left_frame, text="Tax Information", padding=10)
        tax_frame.pack(fill="x", pady=(0, 10))
        self.tax_2024_total_var = tk.StringVar()
        self.tax_2024_paid_var = tk.StringVar()
        self.tax_2025_est_var = tk.StringVar()
        self._create_entry_row(tax_frame, "2024 Total:", self.tax_2024_total_var, 0)
        self._create_entry_row(tax_frame, "2024 Status:", self.tax_2024_paid_var, 1)
        
        # Add dropdown for paid status
        paid_frame = ttk.Frame(tax_frame)
        paid_frame.grid(row=1, column=1, sticky="ew", pady=2)
        self.paid_combo = ttk.Combobox(paid_frame, textvariable=self.tax_2024_paid_var, 
                                       values=["PAID", "UNPAID", "PARTIAL"], 
                                       state="normal", width=28)
        self.paid_combo.pack(side="left")
        
        self._create_entry_row(tax_frame, "2025 Estimated:", self.tax_2025_est_var, 2)

        # --- Title Chain Document ---
        doc_frame = ttk.LabelFrame(left_frame, text="Title Chain Document", padding=10)
        doc_frame.pack(fill="x", pady=(0, 10))
        self.title_doc_var = tk.StringVar()
        doc_row = ttk.Frame(doc_frame)
        doc_row.pack(fill="x")
        ttk.Label(doc_row, text="Abstract File:").pack(side="left")
        self.title_doc_entry = ttk.Entry(doc_row, textvariable=self.title_doc_var, width=40)
        self.title_doc_entry.pack(side="left", fill="x", expand=True, padx=(6,6))
        ttk.Button(doc_row, text="Browse", command=self.browse_title_document).pack(side="left")

        # Drop handler
        def _drop_on_doc(event):
            path = event.data.strip('{}')
            if path.lower().endswith(('.pdf', '.docx')):
                self.title_doc_var.set(path)
                self.process_title_document()
        doc_frame.drop_target_register(DND_FILES)
        doc_frame.dnd_bind("<<Drop>>", _drop_on_doc)

        ttk.Button(doc_frame, text="Process Document", command=self.process_title_document).pack(pady=(5,0))

        # --- Title Chain Summary ---
        title_frame = ttk.LabelFrame(left_frame, text="Title Chain Summary", padding=10)
        title_frame.pack(fill="x", pady=(0, 10))
        self.title_summary_var = tk.StringVar(value="Not loaded yet.")
        ttk.Label(title_frame, textvariable=self.title_summary_var, wraplength=250).pack(anchor="w")
        ttk.Button(title_frame, text="View Details", command=self.view_title_details).pack(pady=(5,0))

        # --- Document Details ---
        doc_details_frame = ttk.LabelFrame(right_frame, text="Document Details", padding=10)
        doc_details_frame.pack(fill="x", pady=(0, 10))
        self.lender_var = tk.StringVar()
        self.borrower_var = tk.StringVar()
        self.loan_amount_var = tk.StringVar()
        self.writer_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self._create_entry_row(doc_details_frame, "Lender:", self.lender_var, 0)
        self._create_entry_row(doc_details_frame, "Borrower:", self.borrower_var, 1)
        self._create_entry_row(doc_details_frame, "Loan Amount:", self.loan_amount_var, 2)
        self._create_entry_row(doc_details_frame, "Writer:", self.writer_var, 3)
        self._create_entry_row(doc_details_frame, "Date:", self.date_var, 4)
        
        # Add default values
        self.writer_var.set("Collin Hawkins")
        from datetime import datetime
        self.date_var.set(datetime.now().strftime("%B %d, %Y"))
        
        # Notes as text widget
        ttk.Label(doc_details_frame, text="Notes:").grid(row=5, column=0, sticky="ne", padx=(0, 5), pady=2)
        self.notes_text = tk.Text(doc_details_frame, width=30, height=3)
        self.notes_text.grid(row=5, column=1, sticky="ew", pady=2)

        # --- Document Generation ---
        doc_gen_frame = ttk.LabelFrame(right_frame, text="Document Generation", padding=10)
        doc_gen_frame.pack(fill="x", pady=(0, 10))
        self.output_path_var = tk.StringVar()
        self._create_entry_row(doc_gen_frame, "Output Path:", self.output_path_var, 0, browse_btn=True)
        self.generate_btn = ttk.Button(doc_gen_frame, text="Generate Document", command=self.generate_document)
        self.generate_btn.grid(row=1, column=1, sticky="w", pady=(10,0))
        self.progress = ttk.Progressbar(doc_gen_frame, mode="indeterminate")
        self.progress.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5,0))

        # --- Load from Tabs Button ---
        load_button = ttk.Button(self, text="Load From Tabs", command=self.load_from_tabs)
        load_button.pack(side="bottom", pady=10)

    def browse_title_document(self):
        path = filedialog.askopenfilename(
            title="Select Title Chain Document", 
            filetypes=[("PDF files","*.pdf"), ("Word documents", "*.docx"), ("All files","*.*")]
        )
        if path:
            self.title_doc_var.set(path)

    def process_title_document(self):
        """Process the title document using improved extraction."""
        file_path = self.title_doc_var.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid title document file.")
            return
        
        self.title_summary_var.set("Processing document...")
        threading.Thread(target=self._process_title_document_thread, args=(file_path,), daemon=True).start()

    def _process_title_document_thread(self, file_path):
        """Thread worker for processing title documents."""
        try:
            print(f"Processing title document: {file_path}")
            
            # Use the improved process_title_document function
            success, msg, chain_deeds = process_title_document(file_path)
            
            if success and chain_deeds:
                self.shared_data.set_data("title_chain_results", chain_deeds)
                summary = f"Found {len(chain_deeds)} vesting deeds in 24-month chain."
                self.after(0, lambda: self.title_summary_var.set(summary))
                print(msg)
            else:
                self.after(0, lambda: self.title_summary_var.set(msg))
                if not success:
                    self.after(0, lambda: messagebox.showerror("Processing Error", msg))
            
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            print(f"Title processing error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda: self.title_summary_var.set("Processing failed."))
            self.after(0, lambda: messagebox.showerror("Processing Error", error_msg))

    def _create_entry_row(self, parent, label_text, var, row, browse_btn=False):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="e", padx=(0, 5), pady=2)
        if label_text != "2024 Status:":  # Skip for the paid status combo
            entry = ttk.Entry(parent, textvariable=var, width=30)
            entry.grid(row=row, column=1, sticky="ew", padx=(0, 5 if browse_btn else 0), pady=2)
        if browse_btn:
            ttk.Button(parent, text="...", width=3, command=self.browse_output).grid(row=row, column=2, pady=2)
        parent.columnconfigure(1, weight=1)

    def load_from_tabs(self):
        """Load data from other tabs into this tab."""
        print("Loading data from tabs...")
        self.pin_var.set(self.shared_data.get_data("parcel_pin") or "")
        self.address_var.set(self.shared_data.get_data("parcel_address") or "")
        self.owner_var.set(self.shared_data.get_data("parcel_owner") or "")
        self.city_var.set(self.shared_data.get_data("parcel_city_state_zip") or "")
        self.legal_desc_var.set(self.shared_data.get_data("parcel_legal_description") or "")
        
        # Tax data
        tax_total = self.shared_data.get_data("tax_2024_total") or ""
        self.tax_2024_total_var.set(tax_total)
        self.tax_2024_paid_var.set(self.shared_data.get_data("tax_2024_paid_status") or "PAID")
        self.tax_2025_est_var.set(self.shared_data.get_data("tax_2025_estimated") or "")

        # Title chain
        results = self.shared_data.get_data("title_chain_results")
        if results:
            self.title_summary_var.set(f"{len(results)} vesting deeds found.")
            print(f"Loaded {len(results)} title chain results")
        else:
            self.title_summary_var.set("No title chain data found.")

    def view_title_details(self):
        results = self.shared_data.get_data("title_chain_results")
        if not results:
            messagebox.showinfo("Title Chain Details", "No title chain data has been loaded.")
            return

        details_win = tk.Toplevel(self)
        details_win.title("Title Chain Details")
        details_win.geometry("800x400")

        cols = ("Date", "Grantor", "Grantee", "Instrument", "Book-Page")
        tree = ttk.Treeview(details_win, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="w")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for deed in results:
            tree.insert("", "end", values=(deed.date_string, deed.grantor, deed.grantee, deed.instrument, deed.book_page))

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save Document As",
            defaultextension=".docx",
            filetypes=[("Word documents", "*.docx"), ("All files", "*.*")],
        )
        if path:
            self.output_path_var.set(path)

    def generate_document(self):
        # Determine output path
        doc_path = (self.title_doc_var.get() or "").strip()
        out_path = self.output_path_var.get().strip()

        if doc_path:
            try:
                gp = os.path.abspath(os.path.join(os.path.dirname(doc_path), os.pardir))
                output_path = os.path.join(gp, "TitleDocs.docx")
            except Exception:
                output_path = out_path or os.path.abspath("TitleDocs.docx")
        else:
            output_path = out_path or os.path.abspath("TitleDocs.docx")

        self.generate_btn.config(state="disabled")
        self.progress.start()

        threading.Thread(target=self._generate_document_thread, args=(output_path,), daemon=True).start()

    def _generate_document_thread(self, output_path):
        try:
            success, msg = self._create_full_document(output_path)
            if success:
                self.after(0, lambda: messagebox.showinfo("Success", msg))
            else:
                self.after(0, lambda: messagebox.showerror("Error", msg))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"An unexpected error occurred: {e}"))
        finally:
            self.after(0, self.progress.stop)
            self.after(0, lambda: self.generate_btn.config(state="normal"))

    def get_template_path(self):
        try:
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            path = os.path.join(current_dir, "templates", "td_tmplt2.docx")
            return path if os.path.exists(path) else None
        except Exception:
            return None

    def _create_full_document(self, output_path):
        """Create the final document with proper placeholder mapping."""
        template_path = self.get_template_path()
        if not template_path:
            return False, "Template file 'td_tmplt2.docx' not found."

        # Get notes from text widget
        notes_text = self.notes_text.get("1.0", "end-1c")

        # Process title document if not already done
        doc_path = (self.title_doc_var.get() or "").strip()
        if doc_path and os.path.exists(doc_path):
            current_results = self.shared_data.get_data("title_chain_results")
            if not current_results:
                print("Processing title document for generation...")
                from desoto.services.title_chain import process_title_document
                success, msg, chain_deeds = process_title_document(doc_path)
                if success:
                    self.shared_data.set_data("title_chain_results", chain_deeds)

        doc = Document(template_path)

        # CRITICAL: Map UI fields to template placeholders correctly
        placeholders = {
            # Property placeholders
            "{PARCEL}": self.pin_var.get(),
            "{PROPSTRE}": self.address_var.get(),  # Property Street
            "{SLRLAST}": self.owner_var.get(),     # Seller Last Name
            "{CITY_STATE_ZIP}": self.city_var.get(),
            "{LEGAL_DESC}": self.legal_desc_var.get(),
            
            # Tax placeholders
            "{TAXAMT}": self.tax_2024_total_var.get(),  # 2024 Tax Amount
            "{TAX_2024_PAID}": self.tax_2024_paid_var.get(),
            "{TAX_2025_EST}": self.tax_2025_est_var.get(),
            
            # Document details placeholders
            "{Lender}": self.lender_var.get(),
            "{BYRLAST}": self.borrower_var.get(),  # Buyer Last Name
            "{LOAN_AMOUNT}": self.loan_amount_var.get(),
            "{WRITER}": self.writer_var.get(),
            "{DATE}": self.date_var.get(),
            "{NOTES}": notes_text,
        }

        # Replace placeholders in paragraphs
        for paragraph in doc.paragraphs:
            for placeholder, value in placeholders.items():
                if placeholder in paragraph.text:
                    # Preserve formatting while replacing
                    for run in paragraph.runs:
                        if placeholder in run.text:
                            run.text = run.text.replace(placeholder, value or "")

        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for placeholder, value in placeholders.items():
                            if placeholder in paragraph.text:
                                for run in paragraph.runs:
                                    if placeholder in run.text:
                                        run.text = run.text.replace(placeholder, value or "")

        # Fill Title Chain Table
        chain_deeds = self.shared_data.get_data("title_chain_results") or []
        
        # Find the chain table
        chain_table = None
        for table in doc.tables:
            if len(table.rows) > 0:
                header_text = ' '.join([cell.text.upper() for cell in table.rows[0].cells])
                if 'GRANTOR' in header_text and 'GRANTEE' in header_text:
                    chain_table = table
                    break

        if chain_table and chain_deeds:
            # Clear existing data rows (keep header)
            while len(chain_table.rows) > 1:
                chain_table._element.remove(chain_table.rows[-1]._element)

            # Add chain data
            for deed in chain_deeds:
                row = chain_table.add_row()
                cells = row.cells
                if len(cells) >= 5:
                    cells[0].text = deed.grantor
                    cells[1].text = deed.grantee
                    cells[2].text = deed.instrument
                    cells[3].text = deed.date_string
                    cells[4].text = deed.book_page

            print(f"Added {len(chain_deeds)} deeds to chain table")

        doc.save(output_path)
        return True, f"Document successfully generated at:\n{output_path}"