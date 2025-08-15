import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
from desoto.data import SharedData
from desoto.gui import ParcelTab, TaxTab, ProcessingTab


class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.configure(bg="#f0f0f0") # Set a light gray background

        self.title("DeSoto County Utility")
        self.geometry("1024x768") # Modern screen size
        self.resizable(True, True)

        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # Modern styling
        self.style = ttk.Style(self)
        self.style.theme_use("clam")  # Use a modern, flat theme

        # Consistent font throughout the app
        font_family = "Segoe UI"
        font_size = 10
        self.option_add("*Font", (font_family, font_size))

        # Configure widget styles with more padding and modern look
        self.style.configure("TNotebook", tabposition="n")
        self.style.configure("TNotebook.Tab", padding=(20, 10), font=(font_family, font_size, "bold"))
        self.style.configure("TButton", padding=(12, 8), font=(font_family, font_size))
        self.style.configure("TLabel", padding=5)
        self.style.configure("TLabelframe", padding=15, relief="solid", borderwidth=1)
        self.style.configure("TLabelframe.Label", font=(font_family, 11, "bold"), padding=(0, 5))
        self.style.configure("TEntry", padding=(8, 5))
        self.style.configure("TCombobox", padding=(8, 5))


        self.shared_data = SharedData()

        nb = ttk.Notebook(self)
        nb.pack(expand=True, fill="both", padx=15, pady=15)

        # Create tabs
        processing_tab = ProcessingTab(nb, self.shared_data)
        parcel_tab = ParcelTab(nb, self.shared_data, processing_tab)
        tax_tab = TaxTab(nb, self.shared_data, processing_tab)
        
        # Add tabs to notebook
        nb.add(parcel_tab, text="Parcel Finder")
        nb.add(tax_tab, text="Tax Calculator")
        nb.add(processing_tab, text="Processing")


if __name__ == "__main__":
    App().mainloop()