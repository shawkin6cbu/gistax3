import ttkbootstrap as ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
from desoto.data import SharedData
from desoto.gui import ParcelTab, TaxTab, ProcessingTab


class App(ttk.Window, TkinterDnD.Tk):
    def __init__(self):
        super().__init__(themename="cyborg")

        self.title("TitleDocs")
        self.geometry("1024x768") # Modern screen size
        self.resizable(True, True)

        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

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