import os
import sys
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QStatusBar
)
from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtGui import QFontDatabase
import mame_softlist

SETTINGS_FILE = "settings.json"


class GameListGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = {}
        self.software_list = {}
        self.load_settings()
        self.init_ui()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = {}
        else:
            self.settings = {}

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def init_ui(self):
        self.setWindowTitle("Gamelist Generator")
        self.resize(1000, 650)

        geom_data = self.settings.get("window_geometry", None)
        if isinstance(geom_data, str):
            try:
                geom = QByteArray.fromHex(geom_data.encode("ascii"))
                self.restoreGeometry(geom)
            except Exception:
                pass

        layout = QVBoxLayout()

        # ROM path
        rom_layout = QHBoxLayout()
        rom_layout.addWidget(QLabel("ROM Path:"))
        self.ent_rom = QLineEdit(self.settings.get("rom_path", ""))
        btn_browse_rom = QPushButton("Browse")
        btn_browse_rom.clicked.connect(self.browse_rom)
        rom_layout.addWidget(self.ent_rom)
        rom_layout.addWidget(btn_browse_rom)
        layout.addLayout(rom_layout)

        # Output directory
        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Base Gamelist Folder (e.g. ES-DE/gamelists):"))
        self.ent_output = QLineEdit(
            self.settings.get(
                "output_directory",
                r"D:\Emulators\EmulationStation-DE\ES-DE\gamelists",
            )
        )
        btn_browse_out = QPushButton("Browse")
        btn_browse_out.clicked.connect(self.browse_output)
        out_layout.addWidget(self.ent_output)
        out_layout.addWidget(btn_browse_out)
        layout.addLayout(out_layout)

        # Extensions
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("File extensions (comma separated):"))
        self.ent_ext = QLineEdit(self.settings.get("extensions", ".zip"))
        ext_layout.addWidget(self.ent_ext)
        layout.addLayout(ext_layout)

        # Options
        self.chk_recursive = QCheckBox("Scan subdirectories recursively (follow symlinks)")
        self.chk_recursive.setChecked(self.settings.get("recursive", False))
        self.chk_recursive.stateChanged.connect(self.load_roms)
        layout.addWidget(self.chk_recursive)

        self.chk_fullpath = QCheckBox("Use full ROM paths in XML")
        self.chk_fullpath.setChecked(self.settings.get("use_fullpath", False))
        layout.addWidget(self.chk_fullpath)

        self.chk_softlist = QCheckBox("Use MAME Software List Names")
        self.chk_softlist.setChecked(self.settings.get("use_softlist", False))
        self.chk_softlist.stateChanged.connect(self.load_roms)
        layout.addWidget(self.chk_softlist)

        # Softlist file
        soft_layout = QHBoxLayout()
        soft_layout.addWidget(QLabel("Softlist XML:"))
        self.ent_softlist = QLineEdit(self.settings.get("softlist_file", ""))
        btn_browse_softlist = QPushButton("Browse")
        btn_browse_softlist.clicked.connect(self.browse_softlist)
        soft_layout.addWidget(self.ent_softlist)
        soft_layout.addWidget(btn_browse_softlist)
        layout.addLayout(soft_layout)

        # Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Exclude", "ROM Path", "Name"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_generate = QPushButton("Generate Gamelist")
        self.btn_generate.clicked.connect(self.generate_gamelist)
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_fields)
        btn_layout.addWidget(self.btn_generate)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

        self.setLayout(layout)
        self.apply_theme()
        self.load_roms()

    def apply_theme(self):
        try:
            QFontDatabase.addApplicationFont("aldrich.ttf")
        except Exception:
            pass

        self.setStyleSheet(
            """
            QWidget {
                background-color: black;
                color: #00FF00;
                font-family: Aldrich, monospace;
                font-size: 12pt;
            }
            QLineEdit, QTableWidget, QTableCornerButton::section {
                background-color: black;
                color: #00FF00;
                selection-background-color: #003300;
                selection-color: #00FF00;
            }
            QHeaderView::section {
                background-color: #001100;
                color: #00FF00;
                border: 1px solid #003300;
            }
            QTableWidget::item {
                background-color: black;
                color: #00FF00;
            }
            QTableWidget::item:alternate {
                background-color: #001100;
                color: #00FF00;
            }
            QPushButton {
                background-color: black;
                color: #00FF00;
                border: 2px solid #00FF00;
                padding: 4px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #003300;
            }
            QCheckBox {
                color: #00FF00;
            }
        """
        )

    def browse_rom(self):
        path = QFileDialog.getExistingDirectory(self, "Select ROM Directory")
        if path:
            self.ent_rom.setText(path)
            self.settings["rom_path"] = path
            self.save_settings()
            self.load_roms()

    def browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.ent_output.setText(path)
            self.settings["output_directory"] = path
            self.save_settings()

    def browse_softlist(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select MAME Softlist XML", "", "XML Files (*.xml)")
        if file:
            self.ent_softlist.setText(file)
            self.settings["softlist_file"] = file
            self.save_settings()
            try:
                self.software_list = mame_softlist.load_softlist(file)
            except Exception as e:
                print(f"Failed to load softlist.xml: {e}")
                self.software_list = {}
            self.load_roms()

    def load_roms(self):
        self.table.setRowCount(0)
        rom_dir = self.ent_rom.text().strip()
        if not rom_dir or not os.path.isdir(rom_dir):
            return

        exts_raw = (self.ent_ext.text() or ".zip").strip().lower()
        exts = [e.strip() for e in exts_raw.split(",") if e.strip()]
        exts = [(e if e.startswith(".") else "." + e) for e in exts]

        use_softlist = self.chk_softlist.isChecked()
        softlist = {k.lower(): v for k, v in self.software_list.items()} if use_softlist else {}

        recursive = self.chk_recursive.isChecked()

        if recursive:
            for root, dirs, files in os.walk(rom_dir, followlinks=True):
                for file in sorted(files):
                    if any(file.lower().endswith(ext) for ext in exts):
                        self.add_table_row(root, file, softlist)
        else:
            for file in sorted(os.listdir(rom_dir)):
                if any(file.lower().endswith(ext) for ext in exts):
                    self.add_table_row(rom_dir, file, softlist)

    def add_table_row(self, root, file, softlist):
        base = os.path.splitext(file)[0].lower()
        display_name = softlist.get(base, base)
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Exclude checkbox
        chk = QTableWidgetItem()
        chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        chk.setCheckState(Qt.Unchecked)
        self.table.setItem(row, 0, chk)

        # ROM path (locked)
        path_item = QTableWidgetItem(os.path.join(root, file))
        path_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.table.setItem(row, 1, path_item)

        # Name (editable)
        name_item = QTableWidgetItem(display_name)
        name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
        self.table.setItem(row, 2, name_item)

    def generate_gamelist(self):
        rom_dir = self.ent_rom.text().strip()
        if not rom_dir:
            self.status_bar.showMessage("No ROM directory set.", 5000)
            return

        output_base = self.ent_output.text().strip()
        if not output_base:
            self.status_bar.showMessage("No output directory set.", 5000)
            return

        rom_base_name = os.path.basename(os.path.normpath(rom_dir))
        system_output_path = os.path.join(output_base, rom_base_name)
        try:
            os.makedirs(system_output_path, exist_ok=True)
        except Exception as e:
            self.status_bar.showMessage(f"Failed to create output folder: {e}", 5000)
            return

        gamelist_file = os.path.join(system_output_path, "gamelist.xml")

        root_elem = ET.Element("gameList")
        games_written = 0

        for row in range(self.table.rowCount()):
            chk_item = self.table.item(row, 0)
            path_item = self.table.item(row, 1)
            name_item = self.table.item(row, 2)

            if chk_item is not None and chk_item.checkState() == Qt.Checked:
                continue
            if not path_item or not name_item:
                continue

            path_text = path_item.text().strip()
            name_text = name_item.text().strip()

            game = ET.SubElement(root_elem, "game")
            if self.chk_fullpath.isChecked():
                ET.SubElement(game, "path").text = path_text
            else:
                ET.SubElement(game, "path").text = f"./{os.path.basename(path_text)}"
            ET.SubElement(game, "name").text = name_text
            ET.SubElement(game, "desc").text = ""
            games_written += 1

        if games_written == 0:
            self.status_bar.showMessage("No ROMs found → skipping gamelist.xml.", 5000)
            return

        try:
            tree = ET.ElementTree(root_elem)
            try:
                ET.indent(tree, space="  ")
                tree.write(gamelist_file, encoding="utf-8", xml_declaration=True)
            except Exception:
                xml_bytes = ET.tostring(root_elem, encoding="utf-8")
                pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ")
                with open(gamelist_file, "w", encoding="utf-8") as f:
                    f.write(pretty)
        except Exception as e:
            self.status_bar.showMessage(f"Write error: {e}", 5000)
            return

        self.status_bar.showMessage(
            f"Wrote gamelist.xml with {games_written} entries → {gamelist_file}", 10000
        )

    def clear_fields(self):
        self.ent_rom.clear()
        self.ent_output.clear()
        self.ent_softlist.clear()
        self.ent_ext.setText(".zip")
        self.chk_softlist.setChecked(False)
        self.chk_recursive.setChecked(False)
        self.chk_fullpath.setChecked(False)
        self.table.setRowCount(0)

    def closeEvent(self, event):
        self.settings["rom_path"] = self.ent_rom.text()
        self.settings["output_directory"] = self.ent_output.text()
        self.settings["softlist_file"] = self.ent_softlist.text()
        self.settings["extensions"] = self.ent_ext.text()
        self.settings["use_softlist"] = self.chk_softlist.isChecked()
        self.settings["recursive"] = self.chk_recursive.isChecked()
        self.settings["use_fullpath"] = self.chk_fullpath.isChecked()
        try:
            self.settings["window_geometry"] = self.saveGeometry().toHex().data().decode("ascii")
        except Exception:
            pass
        self.save_settings()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameListGenerator()
    window.show()
    sys.exit(app.exec_())
