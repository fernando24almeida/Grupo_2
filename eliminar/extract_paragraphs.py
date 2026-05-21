import xml.etree.ElementTree as ET
import os

xml_file = r'C:\Grupo_2\temp_docx_extraction\extracted\word\document.xml'
tree = ET.parse(xml_file)
root = tree.getroot()

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Find all paragraph nodes
paragraphs = root.findall('.//w:p', ns)

for i, p in enumerate(paragraphs):
    texts = p.findall('.//w:t', ns)
    text = ''.join([node.text for node in texts if node.text])
    if text.strip():
        print(f"[{i}] {text}")
