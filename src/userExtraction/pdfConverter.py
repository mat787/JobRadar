from PyPDF2 import PdfReader


class PdfTextExtractor:

    def __init__(self, filepath):
        self.filepath = filepath

    def get_text(self):
        extracted_pages = []

        with open(self.filepath, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_pages.append(text)

        return "\n".join(extracted_pages)

