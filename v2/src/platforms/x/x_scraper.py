from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, ClassVar
from .selenium_twitter_scraper.scraper import run_twitter_scraper


class TwitterScraperInput(BaseModel):
    scrape_type: str = Field(description="Type of scraping: 'profile', 'hashtag', 'query', or 'advanced'")
    target: Optional[str] = Field(description="Target username, hashtag, or query string (optional for advanced)")
    tweet_count: int = Field(description="Number of tweets to scrape", default=100)
    latest: bool = Field(description="Scrape the latest tweets", default=False)
    top: bool = Field(description="Scrape the top tweets", default=False)
    min_replies: Optional[int] = Field(description="Minimum number of replies for advanced search", default=None)
    until_date: Optional[str] = Field(description="End date for advanced search in YYYY-MM-DD format", default=None)
    since_date: Optional[str] = Field(description="Start date for advanced search in YYYY-MM-DD format", default=None)

class TwitterScraperOutput(BaseModel):
    success: bool = Field(description="Whether the scraping was successful")
    message: Optional[str] = Field(description="Message indicating the result or error")

class TwitterScraperTool(BaseTool):
    name: ClassVar[str] = "twitter_scraper"
    description: ClassVar[str] = "Performs Twitter scraping based on specified parameters."
    args_schema: Type[BaseModel] = TwitterScraperInput

    def _run(self, scrape_type: str, target: Optional[str], tweet_count: int, latest: bool, top: bool,
             min_replies: Optional[int], until_date: Optional[str], since_date: Optional[str]) -> TwitterScraperOutput:
        try:
            run_twitter_scraper(
                scrape_type=scrape_type,
                target=target,
                tweet_count=tweet_count,
                latest=latest,
                top=top,
                min_replies=min_replies,
                until_date=until_date,
                since_date=since_date
            )
            return TwitterScraperOutput(success=True, message="Scraping completed successfully.")
        except Exception as e:
            return TwitterScraperOutput(success=False, message=f"Error during scraping: {str(e)}")

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented for TwitterScraperTool yet.")
