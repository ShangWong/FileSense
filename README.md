# FileSense
![FileSense drawio](https://github.com/user-attachments/assets/9749e341-d37e-4fe3-9976-f9136c0dcc58)

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
    OPENAI_API_KEY=<your_open_ai_api_key>
    OPENAI_BASE_URL=<if you have a custom endpoint>
    OPENAI_MODEL=<your model, default is gpt-4o-mini>
    ```
1. Save the file.
1. Run:
    ```powershell
    python .\app.py
    ```

## Run with offline models

Use following template 
1. Change the model name to align with local running model.
1. Change the port to align with local server.
```txt
OPENAI_API_KEY='phi3.5'
OPENAI_BASE_URL='http://localhost:11434/v1'
OPENAI_MODEL='phi3.5'
```
