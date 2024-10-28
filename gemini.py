import google.generativeai as genai
import time
from google.api_core.exceptions import InternalServerError, DeadlineExceeded, ResourceExhausted
import random
from google.generativeai.types import HarmProbability
from file_handlers import PDFHandler, DOCXHandler, TXTHandler
import os
import logging

from config import GEMINI_API_KEY


class GeminiTranslator:
    def __init__(self, api_key=None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self._setup_logging()
        self._setup_handlers()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _setup_handlers(self):
        self.handlers = {
            '.pdf': PDFHandler(),
            '.docx': DOCXHandler(),
            '.doc': DOCXHandler(),
            '.txt': TXTHandler()
        }

    def translate_file(self, file_path, target_language, pages_to_translate=float('inf'), custom_prompt=""):
        """
        Translate a file to the target language.
        
        Args:
            file_path (str): Path to the input file
            target_language (str): Target language for translation
            pages_to_translate (int): Number of pages to translate (default: all)
            custom_prompt (str): Additional translation instructions
            
        Returns:
            str: Path to the output file
        """
        ext = os.path.splitext(file_path)[1].lower().strip()
        print(self.handlers)
        print(ext)
        print(ext in self.handlers)
        if ext not in self.handlers:
            raise ValueError(f"Unsupported file format: {ext}")

        handler = self.handlers[ext]
        
        try:
            # Read content
            pages = handler.read_file(file_path)
            
            # Translate content
            translated_pages = self._translate_pages(
                pages, 
                target_language, 
                pages_to_translate,
                custom_prompt
            )
            
            # Save translated content
            output_path = file_path.replace(ext, f'_translated_{target_language}{ext}')
            handler.save_file(output_path, translated_pages)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Translation failed: {str(e)}")
            raise

    def _translate_pages(self, pages, target_language, pages_to_translate, custom_prompt):
        translated_pages = []
        prompt = f"Translate the following text to {target_language}. {custom_prompt}"
        
        for page_num, page in enumerate(pages[:pages_to_translate], 1):
            self.logger.info(f"Translating page {page_num}")
            
            chunks = self._split_text(page)
            translated_chunks = []
            
            for chunk in chunks:
                translated_chunk = self._translate_chunk([prompt, chunk])
                translated_chunks.append(translated_chunk)
            
            translated_page = '\n'.join(translated_chunks)
            translated_pages.append(
                f"[PAGE {page_num} START]\n{translated_page}\n[PAGE {page_num} END]"
            )
        
        return '\n\n'.join(translated_pages)

    def _translate_chunk(self, request_data):
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

    def _split_text(self, text):
        chunks = []
        current_chunk = ""
        for line in text.split('\n'):
            if len(current_chunk) + len(line) > 10000:
                chunks.append(current_chunk)
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'
        if current_chunk:
            chunks.append(current_chunk)
        return chunks
