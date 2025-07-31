from abc import ABC, abstractmethod
from collections.abc import Generator
import requests
from bs4 import BeautifulSoup, Tag
from file_helper import JsonHelper
from shared_types import Article

class SkipIteration(Exception):
  pass

class Scraper(ABC):
  _base_scraping_url: str
  _beautiful_soup: BeautifulSoup
  
  def __init__(self, base_scraping_url: str):
    self._base_scraping_url = base_scraping_url
    self._beautiful_soup = self._fetch_url(self._base_scraping_url)
  
  def _fetch_url(self, link: str) -> BeautifulSoup:
    page = requests.get(link)
    soup = BeautifulSoup(page.content, "lxml")
    return soup
  
  def find_required(self, soup: BeautifulSoup, **kwargs) -> Tag:
    tag = soup.find(**kwargs)
    if not isinstance(tag, Tag):
      raise ValueError("unable to find tag! double check your search criteria or the raw html in the document.")
    else:
      return tag
      
  # might be specifying way too much here, in which case i'll generalize as i add more data sources
      
  @abstractmethod
  def extract_links(self) -> Generator[str]:
    pass
  
  @abstractmethod
  def scrape_article(self, link: str) -> Article:
    print(f'scraping {link}')
    pass
  
  def scrape_articles(self) -> Generator[Article]:
    links = self.extract_links()
    for link in links:
      try:
        yield self.scrape_article(link)
      except SkipIteration:
        pass
  
  def scrape_and_store(self, base_write_directory: str) -> None:
    articles = self.scrape_articles()
    for idx, article in enumerate(articles, 1):
      JsonHelper.write_dict_to_json(dict=article, filepath=base_write_directory)
      print(f'Wrote {article} to {base_write_directory}, #{idx}')