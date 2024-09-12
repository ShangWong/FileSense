import os
import dotenv
from openai import OpenAI
from log import get_logger

dotenv.load_dotenv()

client = OpenAI()

CHAT_LOGGER = get_logger("chat")

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

def trim_document_content(document_content, max_chars=10000):
    # Trim the content to the first max_chars characters
    return document_content[:max_chars]

def get_document_suggest_naming(document_content):
    CHAT_LOGGER.info("Start summarizing the document...")
    trimmed_content = trim_document_content(document_content)

    # Define the prompt for summarization
    basicTone = load_prompt("./resources/prompts/basic_tone_naming.txt")
    prompt = load_prompt("./resources/prompts/online_naming.txt")

    prompt += f"Now handle this doc:\n\n{trimmed_content}.\n\n"

    # Call the OpenAI API to get the summary
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": basicTone,
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )

    suggest_name = response.choices[0].message.content
    CHAT_LOGGER.info("Get the suggest naming of Document successfully.")
    return suggest_name

def summarize_document(document_content):
    CHAT_LOGGER.info("Start summarizing the document...")
    trimmed_content = trim_document_content(document_content)

    # Define the prompt for summarization
    basicTone = load_prompt("./resources/prompts/basic_tone.txt")
    prompt = load_prompt("./resources/prompts/online.txt")

    prompt += f"Now handle this doc:\n\n{trimmed_content}.\n\n"

    # Call the OpenAI API to get the summary
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": basicTone,
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