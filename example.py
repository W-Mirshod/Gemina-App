from gemini import GeminiTranslator


def main():
    translator = GeminiTranslator()
    input_file = input("Enter the path to the file you want to translate: ")
    pages_to_translate = int(input("Enter the number of pages to translate: "))
    target_language = input("Enter the target language: ")
    custom_prompt = input("Enter any additional instructions: ")
    output_file = translator.translate_file(
        file_path=input_file,
        target_language=target_language,
        pages_to_translate=pages_to_translate,
        custom_prompt=custom_prompt
    )
    print(f"Translation saved to: {output_file}")


if __name__ == "__main__":
    main()
