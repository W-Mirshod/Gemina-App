import requests
import mimetypes
import os
import base64
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")


class GeminiApp:
    def __init__(self):
        self.API_KEY = API_KEY
        self.BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def gemini_request(self, content, prompt, model="gemini-1.5-flash"):
        url = f"{self.BASE_URL}/{model}:generateContent?key={self.API_KEY}"

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [{
                "parts": [
                    {"text": content},
                    {"text": prompt}
                ]
            }]
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response")
        else:
            return f"Error: {response.status_code} - {response.text}"

    def read_file(self, file_path):
        with open(file_path, 'rb') as file:
            return file.read()

    def process_file(self, file_path, prompt):
        file_type = mimetypes.guess_type(file_path)[0]

        if file_type == 'application/pdf':
            file_content = self.read_file(file_path)
            base64_content = base64.b64encode(file_content).decode('utf-8')

            url = f"{self.BASE_URL}/gemini-1.5-flash:generateContent?key={self.API_KEY}"

            headers = {
                "Content-Type": "application/json"
            }

            data = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "application/pdf",
                                "data": base64_content
                            }
                        }
                    ]
                }]
            }

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text",
                                                                                                      "No response")
            else:
                return f"Error: {response.status_code} - {response.text}"
        else:
            text = self.read_file(file_path).decode('utf-8')
            return self.gemini_request(text, prompt)

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
