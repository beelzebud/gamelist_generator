import xml.etree.ElementTree as ET


def load_softlist(file_path):
    """
    Load a MAME softlist XML file and return a dict:
    { rom_name: description }
    """
    games = {}
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for software in root.findall("software"):
            name = software.get("name", "").strip()
            description_elem = software.find("description")
            if name:
                desc = description_elem.text.strip() if description_elem is not None else name
                games[name.lower()] = desc
    except Exception as e:
        print(f"[mame_softlist] Error loading softlist {file_path}: {e}")
    return games
