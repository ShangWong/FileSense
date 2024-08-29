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

### Run with offline Phi3 model
We tested on a Apple sillion M1 Mac, other NPU PCs should be similar.
1. Install Ollama https://ollama.com/
1. Go to terminial, execute `ollama pull phi3`
1. After the download finished, `ollama serve`
1. In case you want to change the host of ollama, use `export OLLAMA_HOST=127.0.0.1:1234`
1. Put the following content to it, replace `<OPENAI_BASE_URL>` with the ollama host.
    ```txt
    OPENAI_API_KEY='phi3'
    OPENAI_BASE_URL='http://localhost:1234/v1'
    ```
1. Save the file.
1. Run:
    ```powershell
    python .\app.py --offline
    ```