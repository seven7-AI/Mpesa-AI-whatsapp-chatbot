import sys
import os
from dotenv import load_dotenv
from scraper.__main__ import main

def run_twitter_scraper(scrape_type, target=None, tweet_count=100, latest=False, top=False,
                        min_replies=None, until_date=None, since_date=None):
    """
    Run the Twitter scraper with specified parameters.

    Parameters:
    - scrape_type: str, one of 'profile', 'hashtag', 'query', or 'advanced'
    - target: str, the target username, hashtag, or query string (optional for advanced)
    - tweet_count: int, number of tweets to scrape (default is 100)
    - latest: bool, whether to scrape the latest tweets (default is False)
    - top: bool, whether to scrape the top tweets (default is False)
    - min_replies: int, minimum number of replies for advanced search (optional)
    - until_date: str, end date for advanced search in YYYY-MM-DD format (optional)
    - since_date: str, start date for advanced search in YYYY-MM-DD format (optional)
    """

   
    load_dotenv()

   
    mail = os.getenv("TWITTER_MAIL")
    username = os.getenv("TWITTER_USERNAME")
    password = os.getenv("TWITTER_PASSWORD")
    headless_state = os.getenv("HEADLESS", "yes")

    # Define the base arguments
    args = [
        f"--mail={mail}",
        f"--user={username}",
        f"--password={password}",
        f"--headlessState={headless_state}",
        "-t", str(tweet_count),  # Number of tweets to scrape
    ]

    # Construct the advanced query if scrape_type is 'advanced'
    if scrape_type == 'advanced':
        query_parts = []
        if target:
            query_parts.append(f"({target})")
        if min_replies is not None:
            query_parts.append(f"min_replies:{min_replies}")
        if until_date:
            query_parts.append(f"until:{until_date}")
        if since_date:
            query_parts.append(f"since:{since_date}")

        advanced_query = " ".join(query_parts)
        args.extend(["--query", advanced_query])
    elif scrape_type == 'profile':
        args.extend(["-u", target])
    elif scrape_type == 'hashtag':
        args.extend(["-ht", target])
    elif scrape_type == 'query':
        args.extend(["-q", target])
    else:
        raise ValueError("Invalid scrape_type.")

    # Add latest or top tweets arguments if specified
    if latest:
        args.append("--latest")
    if top:
        args.append("--top")

    # Override sys.argv to pass the arguments to the main function
    sys.argv = ["scraper.py"] + args

    # Call the main function
    main()

# Example usage for dynamic advanced search:
# run_twitter_scraper('profile', 'elonmusk', tweet_count=100, latest=True)
# run_twitter_scraper('advanced', target="@elonmusk", min_replies=1000, until_date="2023-08-31", since_date="2020-01-01")


# Scrape tweets containing the hashtag #python
# run_twitter_scraper(
#     scrape_type='hashtag',
#     target='python',  
#     tweet_count=100,  
#     latest=True    
# )


# Scrape tweets related to the query "Artificial Intelligence"
# run_twitter_scraper(
#     scrape_type='query',
#     target='Artificial Intelligence',  
#     tweet_count=100,  
#     latest=True      
# )

