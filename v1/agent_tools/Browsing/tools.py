from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain.agents import Tool
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper

def perform_search(query):
    serper_wrapper = GoogleSerperAPIWrapper()
    search_results = serper_wrapper.run(query)
    return {"response_code": "success", "results": search_results}

class SearchInput(BaseModel):
    query: str = Field(description="The search query to be used.")

class SearchOutput(BaseModel):
    response_code: str = Field(description="Response code for the search.")
    results: list = Field(description="List of search results.")

class SearchTool(BaseTool):
    name = "perform_search"
    description = "Tool for performing a search using Serper."
    args_schema = SearchInput
    result_schema = SearchOutput

    def _run(self, inputs): 
        query = inputs
        return perform_search(query)
