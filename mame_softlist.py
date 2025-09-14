import xml.etree.ElementTree as ET

def parse_softlist(xml_file):
    """
    Parses a MAME software list XML file and returns a dict mapping rom names to full names.

    Args:
        xml_file (str): Path to the software list XML file.

    Returns:
        dict: { 'rom_basename_lower': 'Full Name' }
    """
    mapping = {}
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Iterate over software elements
    for software in root.findall(".//software"):
        name_attr = software.get("name")
        description_elem = software.find("description")
        if name_attr and description_elem is not None and description_elem.text:
            mapping[name_attr.lower()] = description_elem.text.strip()

    return mapping
