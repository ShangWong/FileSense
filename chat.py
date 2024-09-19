import os
import dotenv
from openai import OpenAI
from log import get_logger
from dataclasses import dataclass
from preprocessor import FileType, PreprocessedFile, get_file_extension

dotenv.load_dotenv()

client = OpenAI()

CHAT_LOGGER = get_logger("chat")

@dataclass
class LLMResponse:
    isOriginTitleUsable: bool
    proposedTitle: str
    summary: str

def load_prompt(file_path):
    # Loads the prompt from a text file.
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        CHAT_LOGGER.error(f"Error: The file {file_path} was not found.")
        return ""
    except Exception as e:
        CHAT_LOGGER.error(f"Error: An error occurred while reading the file {file_path}. {e}")
        return ""

def trim_document_content(document_content: str, max_chars=10000):
    # Trim the content to the first max_chars characters
    return document_content[:max_chars]

def create_text_messages(document_content: PreprocessedFile):
    trimmed_content = trim_document_content(document_content.content)

    # Define the prompt for summarization
    basic_tone = load_prompt("./resources/prompts/basic_tone_naming.txt")
    prompt = load_prompt("./resources/prompts/online_naming.txt")

    prompt += f"Now handle this file:\n\n{trimmed_content}.\n\n"

    return [
        {
            "role": "system",
            "content": basic_tone,
        },
        {
            "role": "user",
            "content": prompt,
        }
    ]

def create_image_messages(document_content: PreprocessedFile):
    # Define the prompt for summarization
    basic_tone = load_prompt("./resources/prompts/basic_tone_naming.txt")
    prompt = load_prompt("./resources/prompts/online_naming.txt")

    prompt += f"You will be given an image, now give this image a new name."

    image_type = get_file_extension(document_content.original_name)
    if image_type == "jpg":
        image_type = "jpeg"

    return [
        {
            "role": "system",
            "content": basic_tone,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_type};base64,{document_content.content}"
                    }
                }
            ]
        }
    ]

def get_folder_suggest_naming(file_names: list[str]) -> str:
    files = ",".join(file_names)
    basic_tone_naming = load_prompt("./resources/prompts/basic_tone_naming.txt")
    folder_prompt = load_prompt("./resources/prompts/folder_naming.txt")
    actual_files_prompt = f"We have the following file names in the folder: {files}. Please suggest a folder name, do not explain."

    # Call the OpenAI API to get the summary
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": basic_tone_naming,
            },
            {
                "role": "user",
                "content": folder_prompt,
            },
            {
                "role": "user",
                "content": actual_files_prompt,
            }
        ],
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )

    folder_name = response.choices[0].message.content
    CHAT_LOGGER.info("Folder name was generated successfully.")

    return folder_name

def get_document_suggest_naming(document_content: PreprocessedFile):
    CHAT_LOGGER.info("Start generating the new file name...")
    if document_content.file_type == FileType.TEXT:
        messages = create_text_messages(document_content)
    elif document_content.file_type == FileType.IMAGE:
        messages = create_image_messages(document_content)
    else:
        CHAT_LOGGER.error(f"Unknown file type: {document_content.file_type}. New name generation request won't be sent.")
        return ""

    # Call the OpenAI API to get the summary
    response = client.chat.completions.create(
        messages=messages,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )

    suggest_name = response.choices[0].message.content
    CHAT_LOGGER.info("Get the suggest naming of Document successfully.")
    return suggest_name

def summarize_document(document_content):
    CHAT_LOGGER.info("Start summarizing the document...")
    trimmed_content = trim_document_content(document_content)

    # Define the prompt for summarization
    basic_tone = load_prompt("./resources/prompts/basic_tone.txt")
    prompt = load_prompt("./resources/prompts/online.txt")

    prompt += f"Now handle this doc:\n\n{trimmed_content}.\n\n"

    # Call the OpenAI API to get the summary
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": basic_tone,
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )

    # Extract and print the summary
    summary = response.choices[0].message.content
    CHAT_LOGGER.info("Document was summarized successfully.")
    return summary