# FileSense

## Setup

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

1. Create a new file under the project folder named `.env`.
1. Put the following content to it, replace `<your_open_ai_api_key>` with the actual OpenAI API key.
    ```txt
    OPENAI_API_KEY=<your_open_ai_key>
    OPENAI_BASE_URL=<if you have a custom endpoint>
    ```
1. Save the file.
1. Run:
    ```powershell
    python .\app.py
    ```