import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

load_dotenv()


def get_access_token():
    consumer_key = "eiDkD79ICeFRE1FDiHgCbDMiOvXgp3cj"
    consumer_secret = "BfFwVt1uGLt7Mki3"
    access_token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    headers = {'Content-Type': 'application/json'}
    auth = (consumer_key, consumer_secret)

    try:
        response = requests.get(access_token_url, headers=headers, auth=auth)
        response.raise_for_status()
        result = response.json()
        access_token = result.get('access_token')
        return AccessTokenOutput(access_token=access_token, error_message=None)
    except requests.exceptions.RequestException as e:
        return AccessTokenOutput(access_token=None, error_message=str(e))


class AccessTokenOutput(BaseModel):
    access_token: Optional[str] = Field(description="Generated access token")
    error_message: Optional[str] = Field(description="Error message in case of failure")


class AccessTokenTool(BaseTool):
    name = "get_access_token"
    description = "Use this to generate an access token for authentication"

    def _run(self):
        return get_access_token()
