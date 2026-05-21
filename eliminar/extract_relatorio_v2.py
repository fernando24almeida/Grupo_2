import xml.etree.ElementTree as ET
import os

xml_file = r'C:\Grupo_2\temp_relatorio\word\document.xml'
tree = ET.parse(xml_file)
root = tree.getroot()

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

paragraphs = []
for p in root.findall('.//w:p', ns):
    texts = [t.text for t in p.findall('.//w:t', ns) if t.text]
    if texts:
        paragraphs.append(''.join(texts))

for i, para in enumerate(paragraphs):
    print(f"Paragraph {i}: {para}")
