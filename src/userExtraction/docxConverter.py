import zipfile
import xml.etree.ElementTree as ET

WORD_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


class DocxTextExtractor:

    def __init__(self, filepath):
        self.filepath = filepath

    def get_text(self):
        paragraphs = []
        with zipfile.ZipFile(self.filepath) as docx:
            root = ET.fromstring(docx.read('word/document.xml'))
        for paragraph in root.iter(f'{WORD_NS}p'):
            text = ''.join(node.text or '' for node in paragraph.iter(f'{WORD_NS}t'))
            if text.strip():
                paragraphs.append(text)
        return "\n".join(paragraphs)
