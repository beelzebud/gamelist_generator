import xml.etree.ElementTree as ET


def load_softlist(xml_file):
    """
    Load a MAME software list XML and return a dictionary mapping
    shortname -> description (pretty name).
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    mapping = {}
    for software in root.findall("software"):
        shortname = software.get("name")
        description_elem = software.find("description")
        if shortname and description_elem is not None and description_elem.text:
            mapping[shortname] = description_elem.text.strip()

    return mapping
