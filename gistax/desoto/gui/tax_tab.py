import threading, tkinter as tk
from tkinter import ttk, messagebox
from desoto.services import fetch_total, DISTRICT_OPTIONS


class TaxTab(ttk.Frame):
    def __init__(self, parent, shared_data, processing_tab):
        super().__init__(parent, padding=20)
        self.shared_data = shared_data
        self.processing_tab = processing_tab

        # helper for labels
        def lbl(text, r, c, **kw):
            ttk.Label(self, text=text, anchor="e")\
               .grid(row=r, column=c, sticky="e",
                     padx=(0, 8), pady=kw.get("pady", 4))

        # === 2025 TAX ESTIMATION SECTION ===
        ttk.Label(self, text="2025 Tax Estimation", font=("Segoe UI", 11, "bold"))\
           .grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # ── appraised value ──────────────────────────────────────
        lbl("Appraised value ($):", 1, 0)
        self.value_var = tk.StringVar()
        value_entry = ttk.Entry(self, textvariable=self.value_var, width=18)
        value_entry.grid(row=1, column=1, sticky="w")

        # hitting Enter inside the value field triggers Calculate
        value_entry.bind("<Return>", lambda e: self.calculate_tax())

        # ── district combo ───────────────────────────────────────
        lbl("Tax district:", 2, 0, pady=10)
        self.district_var = tk.StringVar(value=DISTRICT_OPTIONS[0])
        district_cmb = ttk.Combobox(self, textvariable=self.district_var,
                                    values=DISTRICT_OPTIONS, state="readonly",
                                    width=20)
        district_cmb.grid(row=2, column=1, sticky="w")

        # pressing Enter while combo has focus also triggers Calculate
        district_cmb.bind("<Return>", lambda e: self.calculate_tax())

        # ── calculate button & result ────────────────────────────
        self.btn_calc = ttk.Button(self, text="Calculate 2025 Tax",
                                   command=self.calculate_tax)
        self.btn_calc.grid(row=3, column=1, sticky="w", pady=(0, 6))

        self.tax_result = tk.StringVar()
        ttk.Label(self, textvariable=self.tax_result,
                  font=("Segoe UI", 12, "bold"))\
           .grid(row=4, column=0, columnspan=2, pady=10)

        # === SEPARATOR ===
        ttk.Separator(self, orient='horizontal')\
           .grid(row=5, column=0, columnspan=2, sticky="ew", pady=20)

        # === 2024 TAX DATA SECTION ===
        ttk.Label(self, text="2024 Tax Information", font=("Segoe UI", 11, "bold"))\
           .grid(row=6, column=0, columnspan=2, pady=(0, 10))

        # ── 2024 Total Amount ──────────────────────────────────
        lbl("2024 Total ($):", 7, 0)
        self.tax_2024_var = tk.StringVar()
        tax_2024_entry = ttk.Entry(self, textvariable=self.tax_2024_var, width=18)
        tax_2024_entry.grid(row=7, column=1, sticky="w")

        # ── 2024 Paid Status ────────────────────────────────────
        lbl("2024 Status:", 8, 0, pady=10)
        self.paid_2024_var = tk.StringVar(value="PAID")
        paid_cmb = ttk.Combobox(self, textvariable=self.paid_2024_var,
                                values=["PAID", "UNPAID", "PARTIAL"],
                                state="normal", width=20)
        paid_cmb.grid(row=8, column=1, sticky="w")

        # ── Update button for 2024 data ─────────────────────────
        ttk.Button(self, text="Update 2024 Tax Data",
                  command=self.update_2024_data)\
           .grid(row=9, column=1, sticky="w", pady=(10, 0))

        # tidy grid columns
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

    # ── threaded fetch for 2025 tax ─────────────────────────────
    def calculate_tax(self):
        raw = self.value_var.get().replace(",", "").strip()
        if not raw.isdigit():
            messagebox.showerror("Input error", "Enter a numeric appraised value.")
            return

        assessed_val = str(round(int(raw) * 0.75))
        district = self.district_var.get()

        self.btn_calc.config(state="disabled")
        self.tax_result.set(f"Calculating on ${assessed_val} …")
        threading.Thread(target=self._thread,
                         args=(assessed_val, district), daemon=True).start()

    def _thread(self, val, district):
        try:
            total = fetch_total(val, district)
            msg = f"2025 EST: ${total}" if total else "Total not found."
        except Exception as e:
            msg = f"Lookup failed: {e}"
        self.after(0, self._done, msg)

    def _done(self, msg):
        self.tax_result.set(msg)
        self.btn_calc.config(state="normal")
        if "2025 EST: $" in msg:
            tax_amount = msg.replace("2025 EST: $", "")
            self.shared_data.set_data("tax_2025_estimated", tax_amount)
            self.processing_tab.load_from_tabs()

    # ── Update 2024 tax data ────────────────────────────────────
    def update_2024_data(self):
        """Update the 2024 tax data in shared data."""
        tax_2024 = self.tax_2024_var.get().replace(",", "").strip()
        paid_status = self.paid_2024_var.get()
        
        # Validate 2024 amount if provided
        if tax_2024:
            if not tax_2024.replace(".", "").isdigit():
                messagebox.showerror("Input error", "Enter a valid numeric amount for 2024 taxes.")
                return
            
            # Format the amount with commas
            try:
                amount = float(tax_2024)
                formatted = f"{amount:,.2f}"
                self.tax_2024_var.set(formatted)
                tax_2024 = formatted
            except ValueError:
                pass
        
        # Update shared data
        self.shared_data.set_data("tax_2024_total", tax_2024)
        self.shared_data.set_data("tax_2024_paid_status", paid_status)
        
        # Refresh processing tab
        self.processing_tab.load_from_tabs()
        
        messagebox.showinfo("Success", "2024 tax data updated successfully!")