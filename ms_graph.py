import os
import dotenv
import asyncio
from azure.identity import InteractiveBrowserCredentials
from msgraph import GraphServiceClient

dotenv.load_dotenv()


class Graph:
    def __init__(self):
        self._credential = InteractiveBrowserCredentials(client_id=os.getenv("AZURE_APP_CLIENT_ID"))
        self._graph_client = GraphServiceClient(credentials=self._credential, scopes=["https://graph.microsoft.com/Tasks.ReadWrite", "https://graph.microsoft.com/User.Read"])

    async def create_task(self, title: str):
