import xml.etree.ElementTree as ET


def load_softlist(xml_path):
    """
    Parse a MAME softlist XML file into a dict:
      { "romfilename": "Full Game Name", ... }
    """
    result = {}
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for software in root.findall("software"):
            name = software.get("name", "").strip().lower()
            description = software.findtext("description", "").strip()
            if name:
                result[name] = description or name
    except Exception as e:
        print(f"[mame_softlist] Failed to parse {xml_path}: {e}")
    return result
