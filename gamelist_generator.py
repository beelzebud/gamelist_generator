import os
import sys
import json
import tkinter as tk
from tkinter import filedialog, messagebox, font
import xml.etree.ElementTree as ET
from xml.dom import minidom

import mame_softlist


SETTINGS_FILE = "gamelist_settings.json"


class GameListGenerator(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("ESDE Gamelist Generator")
        self.geometry("450x380")
        self.minsize(400, 380)
        self.configure(bg="#121212")

        self.bg_color = "#121212"
        self.text_color = "#00FF00"
        self.entry_bg = "#001100"
        self.button_bg = "#003300"
        self.button_active_bg = "#005500"
        self.highlight_color = "#00FF00"

        self.folder_path = tk.StringVar()
        self.output_folder_path = tk.StringVar()
        self.extensions = tk.StringVar(value=".nes")
        self.recursive = tk.BooleanVar(value=False)
        self.use_softlist = tk.BooleanVar(value=False)
        self.softlist_file = tk.StringVar()
        self.use_full_paths = tk.BooleanVar(value=False)

        self.create_widgets()
        self.configure_grid()
        self.load_settings()

    def create_widgets(self):
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=10, family="Consolas")

        label_opts = {"bg": self.bg_color, "fg": self.text_color, "anchor": "w", "font": default_font}
        entry_opts = {
            "bg": self.entry_bg,
            "fg": self.text_color,
            "insertbackground": self.text_color,
            "font": default_font,
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": self.highlight_color,
            "highlightcolor": self.highlight_color,
        }
        button_opts = {
            "bg": self.button_bg,
            "fg": self.text_color,
            "activebackground": self.button_active_bg,
            "activeforeground": self.text_color,
            "font": default_font,
            "relief": "flat",
            "bd": 0,
            "cursor": "crosshair",
        }
        checkbox_opts = {
            "bg": self.bg_color,
            "fg": self.text_color,
            "font": default_font,
            "activebackground": self.bg_color,
            "activeforeground": self.text_color,
            "selectcolor": self.bg_color,
            "anchor": "w",
        }

        # ROM Directory
        self.lbl_dir = tk.Label(self, text="ROM Directory:", **label_opts)
        self.ent_dir = tk.Entry(self, textvariable=self.folder_path, **entry_opts)
        self.btn_browse = tk.Button(self, text="Browse...", command=self.browse_folder, **button_opts)

        # Gamelist Output Directory
        self.lbl_output_dir = tk.Label(self, text="Base Gamelist Folder (e.g. ES-DE/gamelists):", **label_opts)
        self.ent_output_dir = tk.Entry(self, textvariable=self.output_folder_path, **entry_opts)
        self.btn_output_browse = tk.Button(self, text="Browse...", command=self.browse_output_folder, **button_opts)

        # File extensions
        self.lbl_ext = tk.Label(self, text="File Extensions (e.g. .nes,.sfc,.zip):", **label_opts)
        self.ent_ext = tk.Entry(self, textvariable=self.extensions, width=20, **entry_opts)

        # Recursive checkbox
        self.chk_recursive = tk.Checkbutton(
            self, text="Scan subdirectories recursively", variable=self.recursive, **checkbox_opts
        )

        # Full paths checkbox
        self.chk_fullpaths = tk.Checkbutton(
            self, text="Use full paths in gamelist.xml", variable=self.use_full_paths, **checkbox_opts
        )

        # Softlist checkbox + entry
        self.chk_softlist = tk.Checkbutton(
            self, text="Use MAME software list", variable=self.use_softlist, **checkbox_opts
        )
        self.ent_softlist = tk.Entry(self, textvariable=self.softlist_file, **entry_opts)
        self.btn_softlist_browse = tk.Button(
            self, text="Browse XML...", command=self.browse_softlist, **button_opts
        )

        # Buttons
        self.btn_generate = tk.Button(
            self, text="Generate gamelist.xml", command=self.generate_gamelist, **button_opts
        )
        self.btn_clear = tk.Button(self, text="Clear", command=self.clear_fields, **button_opts)

        # Grid placement
        self.lbl_dir.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 2), columnspan=3)
        self.ent_dir.grid(row=1, column=0, columnspan=2, sticky="we", padx=(15, 2), pady=2)
        self.btn_browse.grid(row=1, column=2, sticky="e", padx=(2, 15), pady=2)

        self.lbl_output_dir.grid(row=2, column=0, sticky="w", padx=15, pady=(10, 2), columnspan=3)
        self.ent_output_dir.grid(row=3, column=0, columnspan=2, sticky="we", padx=(15, 2), pady=2)
        self.btn_output_browse.grid(row=3, column=2, sticky="e", padx=(2, 15), pady=2)

        self.lbl_ext.grid(row=4, column=0, sticky="w", padx=15, pady=(10, 2), columnspan=3)
        self.ent_ext.grid(row=5, column=0, sticky="we", padx=15, pady=2, columnspan=3)
        self.chk_recursive.grid(row=6, column=0, sticky="w", padx=15, pady=(5, 2), columnspan=3)
        self.chk_fullpaths.grid(row=7, column=0, sticky="w", padx=15, pady=(2, 10), columnspan=3)

        self.chk_softlist.grid(row=8, column=0, sticky="w", padx=15, pady=(5, 2), columnspan=3)
        self.ent_softlist.grid(row=9, column=0, columnspan=2, sticky="we", padx=(15, 2), pady=2)
        self.btn_softlist_browse.grid(row=9, column=2, sticky="e", padx=(2, 15), pady=2)

        self.btn_generate.grid(row=10, column=0, sticky="we", padx=15, pady=(15, 10), columnspan=2)
        self.btn_clear.grid(row=10, column=2, sticky="we", padx=15, pady=(15, 10))

    def configure_grid(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(11, weight=1)

    def browse_folder(self):
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.folder_path.set(selected_folder)

    def browse_output_folder(self):
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.output_folder_path.set(selected_folder)

    def browse_softlist(self):
        selected_file = filedialog.askopenfilename(filetypes=[("XML Files", "*.xml")])
        if selected_file:
            self.softlist_file.set(selected_file)

    def clear_fields(self):
        self.folder_path.set("")
        self.output_folder_path.set("")
        self.extensions.set(".nes")
        self.recursive.set(False)
        self.use_softlist.set(False)
        self.softlist_file.set("")
        self.use_full_paths.set(False)

    def save_settings(self):
        settings = {
            "folder_path": self.folder_path.get(),
            "output_folder_path": self.output_folder_path.get(),
            "extensions": self.extensions.get(),
            "recursive": self.recursive.get(),
            "use_softlist": self.use_softlist.get(),
            "softlist_file": self.softlist_file.get(),
            "use_full_paths": self.use_full_paths.get(),
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
            self.folder_path.set(settings.get("folder_path", ""))
            self.output_folder_path.set(settings.get("output_folder_path", ""))
            self.extensions.set(settings.get("extensions", ".nes"))
            self.recursive.set(settings.get("recursive", False))
            self.use_softlist.set(settings.get("use_softlist", False))
            self.softlist_file.set(settings.get("softlist_file", ""))
            self.use_full_paths.set(settings.get("use_full_paths", False))

    def generate_gamelist(self):
        rom_dir = self.folder_path.get()
        gamelist_base = self.output_folder_path.get()
        exts_raw = self.extensions.get().strip().lower()
        recursive = self.recursive.get()

        if not rom_dir or not os.path.isdir(rom_dir):
            messagebox.showerror("Error", "Please select a valid ROM directory.")
            return

        if not gamelist_base or not os.path.isdir(gamelist_base):
            messagebox.showerror("Error", "Please select a valid base gamelist output folder.")
            return

        if not exts_raw:
            messagebox.showerror("Error", "Please enter at least one file extension.")
            return

        exts = [ext.strip() for ext in exts_raw.split(",") if ext.strip()]
        for i, ext in enumerate(exts):
            if not ext.startswith("."):
                messagebox.showerror("Error", f"File extension '{ext}' must start with a dot (e.g., .nes)")
                return
            exts[i] = ext

        roms = []
        rom_base_name = os.path.basename(os.path.normpath(rom_dir))
        output_path = os.path.join(gamelist_base, rom_base_name)

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Collect ROMs
        if recursive:
            for root, _, files in os.walk(rom_dir):
                for filename in sorted(files):
                    if any(filename.lower().endswith(ext) for ext in exts):
                        full_path = os.path.join(root, filename)
                        if self.use_full_paths.get():
                            rom_path = os.path.abspath(full_path)
                        else:
                            relative_path = os.path.relpath(full_path, rom_dir).replace("\\", "/")
                            if not relative_path.startswith("./"):
                                relative_path = "./" + relative_path
                            rom_path = relative_path
                        name = os.path.splitext(filename)[0]
                        roms.append((rom_path, name))
        else:
            for filename in sorted(os.listdir(rom_dir)):
                full_path = os.path.join(rom_dir, filename)
                if os.path.isfile(full_path) and any(filename.lower().endswith(ext) for ext in exts):
                    if self.use_full_paths.get():
                        rom_path = os.path.abspath(full_path)
                    else:
                        rom_path = "./" + filename
                    name = os.path.splitext(filename)[0]
                    roms.append((rom_path, name))

        if not roms:
            messagebox.showinfo("No Files Found", f"No files with extension(s) '{', '.join(exts)}' were found.")
            return

        # Load softlist if enabled
        softlist_map = {}
        if self.use_softlist.get() and self.softlist_file.get():
            try:
                softlist_map = mame_softlist.load_softlist(self.softlist_file.get())
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load softlist XML:\n{e}")
                return

        # Build XML
        root_elem = ET.Element("gameList")
        for path, name in roms:
            game_elem = ET.SubElement(root_elem, "game")
            path_elem = ET.SubElement(game_elem, "path")
            path_elem.text = path

            name_elem = ET.SubElement(game_elem, "name")
            if name in softlist_map:
                name_elem.text = softlist_map[name]
            else:
                name_elem.text = name

        xml_str = ET.tostring(root_elem, encoding="utf-8")
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

        gamelist_file = os.path.join(output_path, "gamelist.xml")
        with open(gamelist_file, "w", encoding="utf-8") as f:
            f.write(pretty_xml)

        self.save_settings()
        messagebox.showinfo("Success", f"gamelist.xml created with {len(roms)} entries in:\n{gamelist_file}")


if __name__ == "__main__":
    app = GameListGenerator()
    app.mainloop()
