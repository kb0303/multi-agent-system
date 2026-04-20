from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print
load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. return Titles, URLs and snippets."""
    results = tavily.search(query, max_results=5)

    formatted_results = []
    
    for r in results["results"]:
        formatted_results.append(f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n")
    return "\n-----\n".join(formatted_results)

@tool("scrape_url")
def scrape_url(url: str) -> str:
    """Scrape the and return clean text content from a given URL for deeper reading."""
    try:
        response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'noscript', 'iframe', 'ads', 'advertisement', 'cookie', 'consent', 'popup', 'modal', 'head']):
            tag.decompose()
        print(f"Scraping URL: {url}")
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Error scraping URL: {str(e)}"
    
# print(web_search.invoke("What is the recent news on war"))

# print(scrape_url.invoke("https://timesofindia.indiatimes.com/world/middle-east/us-israel-iran-war-news-live-updates-ceasefire-israel-airstrike-missile-attack-lebanon-nawaf-salam-donald-trump-pakistan-jd-vance-netanyahu-deal-strait-of-hormuz-blockade-latest-news/liveblog/130293217.cms"))