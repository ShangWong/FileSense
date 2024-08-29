import dotenv
from openai import OpenAI
from preprocessor import Preprocessor

dotenv.load_dotenv()

client = OpenAI()

def trim_document_content(document_content, max_chars=10000):
    """
    Trims the document content to the specified maximum number of characters.
    """
    # Trim the content to the first max_chars characters
    return document_content[:max_chars]


def summarize_document(document_content):
    # Read the content of the file

    # Trim the document content
    trimmed_content = trim_document_content(document_content)

    # Define the prompt for summarization
    basicTone = """You are a professional file handler.
    You must return your handling result in a json format.
    The json you returned must contain the following 2 properties.
    1) summary
    2) actions
    """
    prompt = """
You will read a file, you will give a short summary (up to 200 words), and give next possible actions in an array format.
For example,
1) For a travel plan file, you would give suggestions to set up todos for booking hotels, reserve rental cars;
2) For a visa application form, you would give suggestions to draft an email on personal leave notice mail, and to set up a reminder on preparing documents.

You would return the response in the following example format. Please return a pure json.
{
    "summary": "The file contains a 7-day travel itinerary for New Zealand, starting from October 1, 2024. The itinerary begins with arrival in Auckland and includes visits to key destinations such as Rotorua, Taupo, and Wellington.",
    "actions":
    [
        {
            "action": "renaming",
            "suggest": "2024_10_New_Zealand_Travel_Itinerary"
        },
        {
            "action": "todo",
            "suggest": {
                "status": "Pending",
                "title": "Book Hotels in Rotorua and Wellington",
                "importance": "High",
                "isReminderOn": true,
                "categories": ["Travel", "Accommodation"]
            }
        },
        {
            "action": "todo",
            "suggest": {
                "status": "Pending",
                "title": "Reserve Rental Car",
                "importance": "High",
                "isReminderOn": true,
                "categories": ["Travel", "Transportation"]
            }
        },
        {
            "action": "todo",
            "suggest": {
                "status": "Pending",
                "title": "Pack Hiking Gear",
                "importance": "Medium",
                "isReminderOn": false,
                "categories": ["Packing", "Travel"]
            }
        },
        {
            "action": "mail",
            "suggest": {
                "title": "New Zealand Travel Plans",
                "body": "Hey, just wanted to share our finalized 7-day New Zealand itinerary starting October 1, 2024. Please review and let me know if you have any suggestions or changes!"
            }
        }
    ]
}"""
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
        model="gpt-4o-mini",
    )

    # Extract and print the summary
    summary = response.choices[0].message.content
    print("Summary:\n", summary)
    return summary

# # Specify the path to your document
# file_path = "invoice.txt"
# summarize_document(file_path)
