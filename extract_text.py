import xml.etree.ElementTree as ET
import os

xml_file = r'C:\Grupo_2\temp_docx_extraction\extracted\word\document.xml'
tree = ET.parse(xml_file)
root = tree.getroot()

# Namespaces are usually needed for word docs
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Find all text nodes
text_nodes = root.findall('.//w:t', ns)
full_text = ' '.join([node.text for node in text_nodes if node.text])

print(full_text)
