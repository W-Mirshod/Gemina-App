import os
import base64
import mimetypes
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

class GeminiApp:
    def __init__(self):
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def gemini_request(self, content, prompt):
        response = self.model.generate_content([content, prompt])
        return response.text

    def read_file(self, file_path):
        with open(file_path, 'rb') as file:
            return file.read()

    def process_file(self, file_path, prompt):
        file_type = mimetypes.guess_type(file_path)[0]
        file_content = self.read_file(file_path)

        if file_type == 'application/pdf':
            base64_content = base64.b64encode(file_content).decode('utf-8')
            response = self.model.generate_content([
                prompt,
                {"mime_type": "application/pdf", "data": base64_content}
            ])
        else:
            text = file_content.decode('utf-8')
            response = self.model.generate_content([text, prompt])

        return response.text

    def run(self):
        while True:
            choice = input("Enter 1 to input text, 2 to upload a file, or 'quit' to exit: ")
            if choice.lower() == 'quit':
                break

            if choice == '1':
                text = input("Enter the text: ")
                prompt = input("Enter the prompt for Gemini: ")
                result = self.gemini_request(text, prompt)
            elif choice == '2':
                file_path = input("Enter the file path: ")
                try:
                    prompt = input("Enter the prompt for Gemini: ")
                    result = self.process_file(file_path, prompt)
                except FileNotFoundError:
                    print(f"Error: File not found at {file_path}")
                    continue
            else:
                print("Invalid choice. Please try again.")
                continue

            print(f"Result: {result}\n")


if __name__ == "__main__":
    app = GeminiApp()
    app.run()
