import os
import dotenv
import asyncio
from azure.identity import InteractiveBrowserCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.todo_task import TodoTask
from kiota_abstractions.api_error import APIError

dotenv.load_dotenv()


class Graph:
    def __init__(self):
        self._credential = InteractiveBrowserCredential(client_id=os.getenv("MS_GRAPH_CLIENTID"),
                                                        tenant_id=os.getenv("MS_GRAPH_TENANTID", "common"))
        scopes = os.getenv("MS_GRAPH_SCOPE").split(":")
        self._graph_client = GraphServiceClient(credentials=self._credential,
                                                scopes=scopes)

    async def create_task(self, title: str, categories: list[str]):
        request_body = TodoTask(
            title=title,
            categories=categories
        )
        try:
            default_task_list_id = await self.get_default_task_list_id()
            return await self._graph_client.me.todo.lists.by_todo_task_list_id(default_task_list_id).tasks.post(request_body)
        except APIError as e:
            print(f"Failed to create task: {e}")
            raise

    async def get_default_task_list_id(self):
        task_list = await self.get_task_list()
        return task_list.value[0].id if task_list.value else None

    async def get_task_list(self):
        try:
            return await self._graph_client.me.todo.lists.get()
        except APIError as e:
            print(f"Failed to get task list: {e}")
            raise

# async def main():
#     graph = Graph()
#     await graph.create_task("First task!", ["Important"])

# if __name__ == "__main__":
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(main())
#     finally:
#         loop.close()
