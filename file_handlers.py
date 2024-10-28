from abc import ABC, abstractmethod
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


class FileHandler(ABC):
    @abstractmethod
    def read_file(self, file_path):
        pass

    @abstractmethod
    def save_file(self, file_path, content):
        pass


class PDFHandler(FileHandler):
    def read_file(self, file_path):
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text())
        return pages

    def save_file(self, file_path, content):        
        c = canvas.Canvas(file_path, pagesize=letter)
        pages = content.split('\n\n')
        
        for page_text in pages:
            c.setFont("Helvetica", 12)
            y = 750
            for line in page_text.split('\n'):
                c.drawString(50, y, line)
                y -= 15
            c.showPage()
        
        c.save()


class DOCXHandler(FileHandler):
    def read_file(self, file_path):
        doc = Document(file_path)
        pages = []
        current_page = []
        for para in doc.paragraphs:
            if len(current_page) >= 3000:  # Arbitrary page size
                pages.append('\n'.join(current_page))
                current_page = []
            current_page.append(para.text)
        if current_page:
            pages.append('\n'.join(current_page))
        return pages

    def save_file(self, file_path, content):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        doc = Document()
        paragraphs = content.split('\n\n')  # Split text into paragraphs
        
        for paragraph in paragraphs:
            if paragraph.strip():
                doc.add_paragraph(paragraph)
        
        doc.save(file_path)


class TXTHandler(FileHandler):
    def read_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        # Split into pages based on some criteria (e.g., line count)
        return [content]  # For now, treating as single page

    def save_file(self, file_path, content):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(''.join(content))
