import os
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key='',
)

def trim_document_content(document_content, max_chars=10000):
    """
    Trims the document content to the specified maximum number of characters.
    """
    # Trim the content to the first max_chars characters
    return document_content[:max_chars]


def summarize_document(file_path):
    # Read the content of the file
    with open(file_path, 'r', encoding="utf8", errors='ignore') as file:
        document_content = file.read()
    
    # Trim the document content
    trimmed_content = trim_document_content(document_content)

    # Define the prompt for summarization
    prompt = f"Summarize this doc:\n\n{trimmed_content}.\n\nGive next possible action if any."

    # Call the OpenAI API to get the summary
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-4o-mini",
    )

    # Extract and print the summary
    summary = response.choices[0].message.content
    print("Summary:\n", summary)

# Specify the path to your document
file_path = "C:\\Users\\wangshang\\Downloads\\testfile.txt"
summarize_document(file_path)