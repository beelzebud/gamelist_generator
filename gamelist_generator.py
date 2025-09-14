import os
import sys
import json
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QFileDialog,
    QVBoxLayout, QGridLayout, QMessageBox, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtCore import Qt
from mame_softlist import parse_softlist

SETTINGS_FILE = "settings.json"

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class GameListGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESDE Gamelist Generator")
        self.setMinimumSize(600, 800)
        self.setStyleSheet("background-color: #121212; color: #00FF00;")

        # Load Aldrich font
        font_file = resource_path("aldrich.ttf")
        font_id = QFontDatabase.addApplicationFont(font_file)
        if font_id == -1:
            self.font = QFont("Consolas", 10)
        else:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.font = QFont(family, 10)

        # Variables
        self.folder_path = ""
        self.output_path = ""
        self.extensions = ".nes"
        self.recursive = False
        self.use_full_paths = False
        self.use_softlist = False
        self.softlist_file = ""

        # Load previous settings
        self.load_settings()

        self.init_ui()
        self.populate_preview()

    # ---------- Settings ----------
    def load_settings(self):
        if os.path.isfile(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                self.folder_path = settings.get("folder_path", "")
                self.output_path = settings.get("output_path", "")
                self.extensions = settings.get("extensions", ".nes")
                self.recursive = settings.get("recursive", False)
                self.use_full_paths = settings.get("use_full_paths", False)
                self.use_softlist = settings.get("use_softlist", False)
                self.softlist_file = settings.get("softlist_file", "")
            except Exception as e:
                print(f"Failed to load settings: {e}")

    def save_settings(self):
        settings = {
            "folder_path": self.folder_path,
            "output_path": self.output_path,
            "extensions": self.extensions,
            "recursive": self.recursive,
            "use_full_paths": self.use_full_paths,
            "use_softlist": self.use_softlist,
            "softlist_file": self.softlist_file
        }
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    # ---------- UI ----------
    def init_ui(self):
        layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setSpacing(10)

        def style_browse(btn):
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #003300;
                    color: #00FF00;
                    border: 2px solid #00FF00;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #005500;
                    border: 2px solid #00FF00;
                }
            """)

        # ROM Directory
        lbl_dir = QLabel("ROM Directory:")
        lbl_dir.setFont(self.font)
        self.ent_dir = QLineEdit(self.folder_path)
        self.ent_dir.setFont(self.font)
        self.ent_dir.setStyleSheet("background-color:#001100; color:#00FF00;")
        btn_dir = QPushButton("Browse...")
        btn_dir.setFont(self.font)
        btn_dir.clicked.connect(self.browse_folder)
        style_browse(btn_dir)
        grid.addWidget(lbl_dir, 0, 0, 1, 3)
        grid.addWidget(self.ent_dir, 1, 0, 1, 2)
        grid.addWidget(btn_dir, 1, 2)

        # Output Directory
        lbl_out = QLabel("Base Gamelist Folder (ES-DE/gamelists):")
        lbl_out.setFont(self.font)
        self.ent_output = QLineEdit(self.output_path)
        self.ent_output.setFont(self.font)
        self.ent_output.setStyleSheet("background-color:#001100; color:#00FF00;")
        btn_out = QPushButton("Browse...")
        btn_out.setFont(self.font)
        btn_out.clicked.connect(self.browse_output)
        style_browse(btn_out)
        grid.addWidget(lbl_out, 2, 0, 1, 3)
        grid.addWidget(self.ent_output, 3, 0, 1, 2)
        grid.addWidget(btn_out, 3, 2)

        # Extensions
        lbl_ext = QLabel("File Extensions (e.g., .nes,.sfc,.zip):")
        lbl_ext.setFont(self.font)
        self.ent_ext = QLineEdit(self.extensions)
        self.ent_ext.setFont(self.font)
        self.ent_ext.setStyleSheet("background-color:#001100; color:#00FF00;")
        grid.addWidget(lbl_ext, 4, 0, 1, 3)
        grid.addWidget(self.ent_ext, 5, 0, 1, 3)

        # Checkboxes
        self.chk_recursive = QCheckBox("Scan subdirectories recursively")
        self.chk_recursive.setFont(self.font)
        self.chk_recursive.setStyleSheet("background-color:#121212; color:#00FF00;")
        self.chk_recursive.setChecked(self.recursive)
        self.chk_recursive.stateChanged.connect(self.populate_preview)

        self.chk_full = QCheckBox("Use full paths in gamelist.xml")
        self.chk_full.setFont(self.font)
        self.chk_full.setStyleSheet("background-color:#121212; color:#00FF00;")
        self.chk_full.setChecked(self.use_full_paths)

        self.chk_softlist = QCheckBox("Use MAME Software List for names")
        self.chk_softlist.setFont(self.font)
        self.chk_softlist.setStyleSheet("background-color:#121212; color:#00FF00;")
        self.chk_softlist.setChecked(self.use_softlist)
        self.chk_softlist.stateChanged.connect(self.toggle_softlist)

        grid.addWidget(self.chk_recursive, 6, 0, 1, 3)
        grid.addWidget(self.chk_full, 7, 0, 1, 3)
        grid.addWidget(self.chk_softlist, 8, 0, 1, 3)

        # Softlist file
        self.ent_softlist = QLineEdit(self.softlist_file)
        self.ent_softlist.setFont(self.font)
        self.ent_softlist.setStyleSheet("background-color:#001100; color:#00FF00;")
        self.ent_softlist.setEnabled(self.use_softlist)
        self.btn_softlist = QPushButton("Browse XML...")
        self.btn_softlist.setFont(self.font)
        self.btn_softlist.setEnabled(self.use_softlist)
        self.btn_softlist.clicked.connect(self.browse_softlist)
        style_browse(self.btn_softlist)

        grid.addWidget(QLabel("MAME Software List XML:"), 9, 0, 1, 3)
        grid.addWidget(self.ent_softlist, 10, 0, 1, 2)
        grid.addWidget(self.btn_softlist, 10, 2)

        # Preview Tree
        self.tree_preview = QTreeWidget()
        self.tree_preview.setHeaderLabels(["ROM Path", "Name"])
        self.tree_preview.header().setSectionResizeMode(QHeaderView.Stretch)
        self.tree_preview.setFont(self.font)
        self.tree_preview.setAlternatingRowColors(True)
        self.tree_preview.setStyleSheet("""
            QTreeWidget {
                background-color: #001100;
                color: #00FF00;
                selection-background-color: #005500;
                selection-color: #00FF00;
                alternate-background-color: #002200;
            }
            QHeaderView::section {
                background-color: #000000;
                color: #00FF00;
                padding: 4px;
                border: 1px solid #00FF00;
            }
        """)
        grid.addWidget(self.tree_preview, 11, 0, 1, 3)

        # Action buttons
        self.btn_generate = QPushButton("Generate gamelist.xml")
        self.btn_generate.setFont(self.font)
        self.btn_generate.clicked.connect(self.generate_gamelist)
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setFont(self.font)
        self.btn_clear.clicked.connect(self.clear_fields)

        grid.addWidget(self.btn_generate, 12, 0, 1, 2)
        grid.addWidget(self.btn_clear, 12, 2)

        layout.addLayout(grid)
        self.setLayout(layout)

    # ---------- Browse and toggle ----------
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select ROM Directory", self.folder_path)
        if folder:
            self.folder_path = folder
            self.ent_dir.setText(folder)
            self.populate_preview()
            self.save_settings()

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Base Gamelist Folder", self.output_path)
        if folder:
            self.output_path = folder
            self.ent_output.setText(folder)
            self.save_settings()

    def browse_softlist(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select MAME Software List XML", "", "XML Files (*.xml)")
        if file:
            self.softlist_file = file
            self.ent_softlist.setText(file)
            self.populate_preview()
            self.save_settings()

    def toggle_softlist(self):
        enabled = self.chk_softlist.isChecked()
        self.ent_softlist.setEnabled(enabled)
        self.btn_softlist.setEnabled(enabled)
        self.populate_preview()
        self.save_settings()

    # ---------- Clear fields ----------
    def clear_fields(self):
        self.ent_dir.clear()
        self.ent_output.clear()
        self.ent_ext.setText(".nes")
        self.chk_recursive.setChecked(False)
        self.chk_full.setChecked(False)
        self.chk_softlist.setChecked(False)
        self.ent_softlist.clear()
        self.populate_preview()
        self.save_settings()

    # ---------- Preview ----------
    def populate_preview(self):
        self.tree_preview.clear()
        rom_dir = self.ent_dir.text()
        exts_raw = self.ent_ext.text()
        recursive = self.chk_recursive.isChecked()
        use_softlist = self.chk_softlist.isChecked()
        softlist_file = self.ent_softlist.text()

        if not rom_dir or not os.path.isdir(rom_dir):
            return

        exts = [e.strip().lower() if e.strip().startswith(".") else "."+e.strip().lower()
                for e in exts_raw.split(",") if e.strip()]

        softlist_map = {}
        if use_softlist and softlist_file and os.path.isfile(softlist_file):
            try:
                raw_map = parse_softlist(softlist_file)
                softlist_map = {}
                for k, v in raw_map.items():
                    softlist_map[k.lower()] = v
                    softlist_map[os.path.splitext(k)[0].lower()] = v
            except Exception as e:
                QMessageBox.warning(self, "Softlist Error", f"Failed to load softlist: {e}")

        roms = []
        for root, _, files in os.walk(rom_dir):
            for f in sorted(files):
                if any(f.lower().endswith(ext) for ext in exts):
                    rom_base = os.path.splitext(os.path.basename(f))[0].lower()
                    name = softlist_map.get(rom_base, rom_base)
                    path = os.path.join(root, f) if self.chk_full.isChecked() else os.path.relpath(os.path.join(root, f), rom_dir)
                    path = path.replace("\\","/")
                    if not self.chk_full.isChecked() and not path.startswith("./"):
                        path = "./" + path
                    roms.append((path, name))
            if not recursive:
                break

        for p, n in roms:
            item = QTreeWidgetItem([p, n])
            self.tree_preview.addTopLevelItem(item)

    # ---------- Generate gamelist ----------
    def generate_gamelist(self):
        rom_dir = self.ent_dir.text()
        output_dir = self.ent_output.text()
        exts_raw = self.ent_ext.text()
        recursive = self.chk_recursive.isChecked()
        use_full_paths = self.chk_full.isChecked()
        use_softlist = self.chk_softlist.isChecked()
        softlist_file = self.ent_softlist.text()

        if not rom_dir or not os.path.isdir(rom_dir):
            QMessageBox.critical(self, "Error", "Select a valid ROM directory.")
            return
        if not output_dir or not os.path.isdir(output_dir):
            QMessageBox.critical(self, "Error", "Select a valid base gamelist folder.")
            return

        exts = [e.strip().lower() if e.strip().startswith(".") else "."+e.strip().lower()
                for e in exts_raw.split(",") if e.strip()]

        softlist_map = {}
        if use_softlist and softlist_file and os.path.isfile(softlist_file):
            try:
                raw_map = parse_softlist(softlist_file)
                softlist_map = {}
                for k, v in raw_map.items():
                    softlist_map[k.lower()] = v
                    softlist_map[os.path.splitext(k)[0].lower()] = v
            except Exception as e:
                QMessageBox.warning(self, "Softlist Error", f"Failed to load softlist: {e}")

        rom_base_name = os.path.basename(os.path.normpath(rom_dir))
        final_dir = os.path.join(output_dir, rom_base_name)
        os.makedirs(final_dir, exist_ok=True)

        roms = []
        for root, _, files in os.walk(rom_dir):
            for f in sorted(files):
                if any(f.lower().endswith(ext) for ext in exts):
                    rom_base = os.path.splitext(os.path.basename(f))[0].lower()
                    name = softlist_map.get(rom_base, rom_base)
                    path = os.path.join(root, f) if use_full_paths else os.path.relpath(os.path.join(root, f), rom_dir)
                    path = path.replace("\\","/")
                    if not use_full_paths and not path.startswith("./"):
                        path = "./" + path
                    roms.append((path, name))
            if not recursive:
                break

        gamelist_file = os.path.join(final_dir, "gamelist.xml")
        root_xml = ET.Element("gameList")
        for path, name in roms:
            game = ET.SubElement(root_xml, "game")
            ET.SubElement(game, "path").text = path
            ET.SubElement(game, "name").text = name

        tree = ET.ElementTree(root_xml)
        self.indent_xml(root_xml)
        tree.write(gamelist_file, encoding="utf-8", xml_declaration=True)
        QMessageBox.information(self, "Success", f"gamelist.xml created with {len(roms)} entries:\n{gamelist_file}")
        self.save_settings()

    # ---------- XML indentation ----------
    def indent_xml(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            for child in elem:
                self.indent_xml(child, level+1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameListGenerator()
    window.show()
    sys.exit(app.exec_())
