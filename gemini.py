import os
from dotenv import load_dotenv
import google.generativeai as genai
import time
from google.api_core.exceptions import InternalServerError, DeadlineExceeded, ResourceExhausted
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import random
from google.generativeai.types import HarmCategory, HarmProbability

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

class GeminiApp:
    def __init__(self):
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.default_prompt = "Translate the following text, preserving any **bold** markdown formatting, don't add any other text, just the translated the conten:."

    def process_file(self, file_path, custom_prompt):
        pages = self.extract_pages_from_pdf(file_path)
        translated_pages = []

        full_prompt = f"{self.default_prompt} {custom_prompt}"
        context = ""

        for page_number, page_text in enumerate(pages, start=1):
            translated_pages.append(f"---START PAGE {page_number}---")
            
            chunks = self.split_text(page_text)
            translated_page = []
            
            for chunk in chunks:
                request_data = [
                    full_prompt,
                    f"Previous context: {context}\n\nText to translate: {chunk}"
                ]
                translated_chunk = self.translate_chunk(request_data)
                translated_page.append(translated_chunk)
                
                context = translated_chunk[-500:]
            
            translated_page_text = '\n'.join(translated_page)
            translated_pages.append(translated_page_text)
            
            translated_pages.append(f"---END PAGE {page_number}---")
            
            print(f"Translated page {page_number} of {len(pages)}")

        result_text = '\n'.join(translated_pages)
        output_docx_path = file_path.replace('.pdf', '_translated.docx')
        self.create_docx(output_docx_path, result_text)
        
        return result_text

    def translate_chunk(self, request_data):
        max_retries = 5
        base_delay = 1
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(request_data)
                
                if not response.candidates or not response.candidates[0].content.parts:
                    safety_ratings = response.prompt_feedback.safety_ratings
                    blocked_categories = [rating.category for rating in safety_ratings if rating.probability != HarmProbability.NEGLIGIBLE]
                    warning_message = f"Warning: Content blocked due to: {', '.join(blocked_categories)}"
                    print(warning_message)
                    return warning_message
                
                return response.text
            except ResourceExhausted as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Rate limit exceeded. Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    print("Max retries reached. Please try again later.")
                    return "Error: Rate limit exceeded. Please try again later."
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

    def split_text(self, text, chunk_size=10000):
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
                if line.startswith('---START PAGE') or line.startswith('---END PAGE'):
                    paragraph = doc.add_paragraph(line)
                    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    paragraph.style.font.bold = True
                else:
                    paragraph = doc.add_paragraph()
                    
                    parts = line.split('**')
                    for i, part in enumerate(parts):
                        run = paragraph.add_run(part)
                        if i % 2 == 1:
                            run.bold = True
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

    def extract_pages_from_pdf(self, file_path):
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text())
        return pages

if __name__ == "__main__":
    print("Starting Gemini App...")
    app = GeminiApp()
    app.run()
