import threading, tkinter as tk
from tkinter import ttk
from desoto.services import query_parcels


class ParcelTab(ttk.Frame):
    """Modernized parcel-lookup tab with improved layout and styling."""

    def __init__(self, parent, shared_data, processing_tab):
        super().__init__(parent, padding=20)
        self.shared_data = shared_data
        self.processing_tab = processing_tab

        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Treeview expands vertically

        # --- Search Row ---
        search_frame = ttk.Frame(self)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Address:").grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.addr_var = tk.StringVar()
        self.addr_entry = ttk.Entry(search_frame, textvariable=self.addr_var)
        self.addr_entry.grid(row=0, column=1, sticky="ew")
        self.addr_entry.focus()

        refresh_btn = ttk.Button(search_frame, text="Refresh", command=self.on_refresh)
        refresh_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))

        self.addr_entry.bind("<KeyRelease>", self.on_type)
        self.addr_entry.bind("<Return>", self.on_enter)

        # --- Results List (Treeview) ---
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        cols = ("Address", "PIN")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)
        self.tree.heading("Address", text="Address")
        self.tree.heading("PIN", text="Parcel #")
        self.tree.column("Address", width=500)
        self.tree.column("PIN", width=150, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.bind("<<TreeviewSelect>>", self.on_pick)

        # --- Details Section ---
        details_frame = ttk.LabelFrame(self, text="Parcel Details", padding=15)
        details_frame.grid(row=2, column=0, sticky="ew")
        for i in range(2): details_frame.columnconfigure(i, weight=1 if i==1 else 0)

        def add_row(label_text, r):
            ttk.Label(details_frame, text=label_text).grid(row=r, column=0, sticky="e", padx=(0, 10), pady=4)
            var = tk.StringVar()
            entry = ttk.Entry(details_frame, textvariable=var, state="readonly", width=50)
            entry.grid(row=r, column=1, sticky="w", pady=4)
            return var

        self.parcel_var = add_row("Parcel #:", 0)
        self.address_var = add_row("Address:", 1)
        self.owner1_var = add_row("Owner 1:", 2)
        self.owner2_var = add_row("Owner 2:", 3)
        self.city_var = add_row("City / State ZIP:", 4)
        self.subd_var = add_row("Subdivision:", 5)
        self.lot_var = add_row("Lot:", 6)

        self.results: list[dict] = []

    # ── autocomplete helpers ───────────────────────────────────
    def on_type(self, *_):
        txt = self.addr_var.get()
        if len(txt) < 3:
            self.tree.delete(*self.tree.get_children())
            return
        threading.Thread(target=self.populate, args=(txt,), daemon=True).start()

    def populate(self, text):
        self.results = query_parcels(text)
        self.tree.delete(*self.tree.get_children())
        for i, attr in enumerate(self.results):
            self.tree.insert("", "end", iid=str(i),
                             values=(attr["FULL_ADDR"], attr["PIN"]))

    # ── selection display ───────────────────────────────────────
    def on_pick(self, *_):
        sel = self.tree.selection()
        if not sel:
            return
        attr = self.results[int(sel[0])]
        self.addr_var.set(attr["FULL_ADDR"])
        self.parcel_var.set(attr["PIN"])
        self.address_var.set(attr["FULL_ADDR"])
        owner1 = attr.get("OWNER_NAME", "")
        owner2 = attr.get("SECOND_OWNER", "")
        self.owner1_var.set(owner1)
        self.owner2_var.set(owner2)
        self.city_var.set(f'{attr.get("CITY","")}, {attr.get("STATE","")} {attr.get("ZIP_CODE","")}')
        self.subd_var.set(attr.get("SUBD_NAME",      ""))
        self.lot_var.set(attr.get("LOT",             ""))

        full_owner = owner1
        if owner2:
            full_owner = f"{owner1} & {owner2}"

        self.shared_data.update_data({
            "parcel_pin": attr["PIN"],
            "parcel_address": attr["FULL_ADDR"],
            "parcel_owner": full_owner,
            "parcel_city_state_zip": f'{attr.get("CITY","")}, {attr.get("STATE","")} {attr.get("ZIP_CODE","")}',
            "parcel_legal_description": f'Lot {attr.get("LOT", "")}, {attr.get("SUBD_NAME", "")}',
        })
        # Auto-update processing tab
        self.processing_tab.load_from_tabs()

    # ── Enter selects first result ──────────────────────────────
    def on_enter(self, *_):
        items = self.tree.get_children()
        if items:
            self.tree.selection_set(items[0])
            self.on_pick()

    # ── Refresh clears everything ───────────────────────────────
    def on_refresh(self, *_):
        self.addr_var.set("")
        self.tree.delete(*self.tree.get_children())
        self.parcel_var.set("")
        self.address_var.set("")
        self.owner1_var.set("")
        self.owner2_var.set("")
        self.city_var.set("")
        self.subd_var.set("")
        self.lot_var.set("")
        self.addr_entry.focus()
