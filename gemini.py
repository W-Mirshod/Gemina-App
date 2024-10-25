import os
from dotenv import load_dotenv
import google.generativeai as genai
import time
from google.api_core.exceptions import InternalServerError, DeadlineExceeded
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

class GeminiApp:
    def __init__(self):
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.default_prompt = "Translate the following text:"

    def process_file(self, file_path, custom_prompt):
        text = self.extract_text_from_pdf(file_path)
        chunks = self.split_text(text)
        translated_chunks = []

        full_prompt = f"{self.default_prompt} {custom_prompt}"

        for chunk in chunks:
            request_data = [full_prompt, chunk]
            translated_chunk = self.translate_chunk(request_data)
            translated_chunks.append(translated_chunk)

        result_text = '\n'.join(translated_chunks)
        output_docx_path = file_path.replace('.pdf', '_translated.docx')
        self.create_docx(output_docx_path, result_text)
        
        return result_text

    def translate_chunk(self, request_data):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(request_data)
                return response.text
            except (InternalServerError, DeadlineExceeded) as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return "Error: The Gemini API is currently unresponsive. Please try again later."

    def extract_text_from_pdf(self, file_path):
        reader = PdfReader(file_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        return text

    def split_text(self, text, chunk_size=5000):
        chunks = []
        current_chunk = ""
        for line in text.split('\n'):
            if len(current_chunk) + len(line) > chunk_size:
                chunks.append(current_chunk)
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def create_docx(self, output_path, text):
        doc = Document()
        doc.add_heading('Translated Text', level=1)

        lines = text.split('\n')
        for line in lines:
            if line.strip():
                if line == '---PAGE BREAK---':
                    doc.add_page_break()
                else:
                    paragraph = doc.add_paragraph(line)
                    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    paragraph.style.font.size = Pt(12)

        doc.save(output_path)

    def run(self):
        while True:
            choice = input("Enter 1 to input text, 2 to upload a file, or 'quit' to exit: ")
            if choice.lower() == 'quit':
                break

            if choice == '2':
                file_path = input("Enter the file path: ")
                try:
                    custom_prompt = input("Enter the custom prompt for Gemini: ")
                    result = self.process_file(file_path, custom_prompt)
                    print("Translation completed and saved to Word document.")
                except FileNotFoundError:
                    print(f"Error: File not found at {file_path}")
                    continue
            else:
                print("Invalid choice. Please try again.")
                continue

if __name__ == "__main__":
    app = GeminiApp()
    app.run()
