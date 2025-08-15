import threading, tkinter as tk
from tkinter import ttk, messagebox
from desoto.services import fetch_total, DISTRICT_OPTIONS


class TaxTab(ttk.Frame):
    def __init__(self, parent, shared_data, processing_tab):
        super().__init__(parent, padding=20)
        self.shared_data = shared_data
        self.processing_tab = processing_tab

        # Configure main grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        # --- 2025 TAX ESTIMATION ---
        est_frame = ttk.LabelFrame(self, text="2025 Tax Estimation", padding=15)
        est_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        est_frame.columnconfigure(1, weight=1)

        # Appraised value
        ttk.Label(est_frame, text="Appraised value ($):").grid(row=0, column=0, sticky="e", padx=(0, 10), pady=5)
        self.value_var = tk.StringVar()
        value_entry = ttk.Entry(est_frame, textvariable=self.value_var, width=25)
        value_entry.grid(row=0, column=1, sticky="w", pady=5)
        value_entry.bind("<Return>", lambda e: self.calculate_tax())

        # Tax district
        ttk.Label(est_frame, text="Tax district:").grid(row=1, column=0, sticky="e", padx=(0, 10), pady=5)
        self.district_var = tk.StringVar(value=DISTRICT_OPTIONS[0])
        district_cmb = ttk.Combobox(est_frame, textvariable=self.district_var,
                                    values=DISTRICT_OPTIONS, state="readonly",
                                    width=23)
        district_cmb.grid(row=1, column=1, sticky="w", pady=5)
        district_cmb.bind("<Return>", lambda e: self.calculate_tax())

        # Calculate button & result
        self.btn_calc = ttk.Button(est_frame, text="Calculate 2025 Tax", command=self.calculate_tax)
        self.btn_calc.grid(row=2, column=1, sticky="w", pady=(10, 5))

        self.tax_result = tk.StringVar()
        ttk.Label(est_frame, textvariable=self.tax_result, font=("Segoe UI", 11, "bold"))\
           .grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 0))

        # --- 2024 TAX DATA ---
        tax_2024_frame = ttk.LabelFrame(self, text="2024 Tax Information", padding=15)
        tax_2024_frame.grid(row=1, column=0, sticky="ew")
        tax_2024_frame.columnconfigure(1, weight=1)

        # 2024 Total
        ttk.Label(tax_2024_frame, text="2024 Total ($):").grid(row=0, column=0, sticky="e", padx=(0, 10), pady=5)
        self.tax_2024_var = tk.StringVar()
        tax_2024_entry = ttk.Entry(tax_2024_frame, textvariable=self.tax_2024_var, width=25)
        tax_2024_entry.grid(row=0, column=1, sticky="w", pady=5)

        # 2024 Status
        ttk.Label(tax_2024_frame, text="2024 Status:").grid(row=1, column=0, sticky="e", padx=(0, 10), pady=5)
        self.paid_2024_var = tk.StringVar(value="PAID")
        paid_cmb = ttk.Combobox(tax_2024_frame, textvariable=self.paid_2024_var,
                                values=["PAID", "UNPAID", "PARTIAL"],
                                state="normal", width=23)
        paid_cmb.grid(row=1, column=1, sticky="w", pady=5)

        # 2024 Date Paid
        ttk.Label(tax_2024_frame, text="Date Paid:").grid(row=2, column=0, sticky="e", padx=(0, 10), pady=5)
        self.date_paid_2024_var = tk.StringVar()
        ttk.Entry(tax_2024_frame, textvariable=self.date_paid_2024_var, width=25).grid(row=2, column=1, sticky="w", pady=5)

        # Auto-sync Processing tab when values change
        self._bind_autosave()

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

    # ── Auto-sync handlers ──────────────────────────────────────
    def _bind_autosave(self):
        # Bind variable traces to auto-update shared data and refresh Processing tab
        def on_amount(*_):
            value = (self.tax_2024_var.get() or "").strip()
            self.shared_data.set_data("tax_2024_total", value)
            self.processing_tab.load_from_tabs()
        def on_status(*_):
            value = (self.paid_2024_var.get() or "").strip()
            self.shared_data.set_data("tax_2024_paid_status", value)
            self.processing_tab.load_from_tabs()
        def on_date_paid(*_):
            value = (self.date_paid_2024_var.get() or "").strip()
            self.shared_data.set_data("tax_2024_date_paid", value)
            self.processing_tab.load_from_tabs()

        # Use trace_add if available; fallback to trace
        try:
            self.tax_2024_var.trace_add('write', on_amount)  # type: ignore[attr-defined]
            self.paid_2024_var.trace_add('write', on_status)  # type: ignore[attr-defined]
            self.date_paid_2024_var.trace_add('write', on_date_paid)  # type: ignore[attr-defined]
        except Exception:
            self.tax_2024_var.trace('w', lambda *_: on_amount())
            self.paid_2024_var.trace('w', lambda *_: on_status())
            self.date_paid_2024_var.trace('w', lambda *_: on_date_paid())