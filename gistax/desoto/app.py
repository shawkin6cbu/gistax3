import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
from desoto.data import SharedData
from desoto.gui import ParcelTab, TaxTab, ProcessingTab


class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("DeSoto County Utility")
        self.geometry("960x640") # Slightly wider for modern layout
        self.resizable(True, True)

        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # Modern styling
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except Exception:
            style.theme_use("clam")
        style.configure("TNotebook.Tab", padding=(14, 8))
        style.configure("TButton", padding=(10, 6))
        style.configure("TLabel", padding=(2, 2))
        style.configure("TLabelframe", padding=10)
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        self.option_add("*Font", ("Segoe UI", 10))

        self.shared_data = SharedData()

        nb = ttk.Notebook(self)
        nb.pack(expand=True, fill="both", padx=8, pady=8)

        # Create tabs
        processing_tab = ProcessingTab(nb, self.shared_data)
        parcel_tab = ParcelTab(nb, self.shared_data, processing_tab)
        tax_tab = TaxTab(nb, self.shared_data, processing_tab)
        
        # Add tabs to notebook
        nb.add(parcel_tab, text="Parcel Finder")
        nb.add(tax_tab, text="Tax Calculator")
        nb.add(processing_tab, text="Processing")  # Fixed indentation


if __name__ == "__main__":
    App().mainloop()
