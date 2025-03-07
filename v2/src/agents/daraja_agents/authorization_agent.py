from langchain.tools import BaseTool
import requests
from pydantic import BaseModel, Field, Optional
from src.config.env import MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET

class AuthorizationOutput(BaseModel):
    access_token: Optional[str] = Field(description="The fetched access token")
    error_message: Optional[str] = Field(description="Error message if token fetch fails")

class AuthorizationAgent(BaseTool):
    name = "get_access_token"
    description = "Fetches an Mpesa Daraja API access token."

    def _run(self) -> AuthorizationOutput:
        auth_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth = (MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET)
        try:
            response = requests.get(auth_url, auth=auth)
            response.raise_for_status()
            return AuthorizationOutput(access_token=response.json().get("access_token"), error_message=None)
        except requests.exceptions.RequestException as e:
            return AuthorizationOutput(access_token=None, error_message=f"Failed to get access token: {str(e)}")