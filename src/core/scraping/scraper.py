from abc import ABC, abstractmethod
from collections.abc import Generator

import requests
from bs4 import BeautifulSoup, Tag
from concurrent.futures import ThreadPoolExecutor

from shared_types import Article

class SkipIteration(Exception):
  def __init__(self, title: str):
    print(f'Skipped {title} because the document has been retired!')
  
  pass

class ParseException(Exception):
  pass

class SoupScraper:
  _base_scraping_url: str
  _beautiful_soup: BeautifulSoup
  
  def __init__(self, base_scraping_url: str):
    self._base_scraping_url = base_scraping_url
    self._beautiful_soup = self._fetch_url(self._base_scraping_url)
  
  def _fetch_url(self, link: str) -> BeautifulSoup:
    page = requests.get(link)
    soup = BeautifulSoup(page.content, "lxml")
    return soup
  
  def find_required(self, soup: BeautifulSoup | None = None, **kwargs) -> Tag:
    if soup is None:
      soup = self._beautiful_soup
    
    tag = soup.find(**kwargs)
    if not isinstance(tag, Tag):
      raise ValueError("unable to find tag! double check your search criteria or the raw html in the document.")
    else:
      return tag

# TODO: add multithreading? scraping takes ~30 minutes right now for 1.8k articles of 12k words each
class _BaseScraper(ABC, SoupScraper):
  def __init__(self, base_scraping_url: str):
    super().__init__(base_scraping_url)
  
  # might be specifying way too much here, in which case i'll generalize as i add more data sources

  @abstractmethod
  def extract_links(self) -> Generator[str]:
    pass
  
  @abstractmethod
  def scrape_article(self, link: str) -> Article:
    print(f'scraping {link}')
    pass
  
  def scrape_articles(self, max_workers: int = 10) -> Generator[Article]:
    links = self.extract_links()
    
    with ThreadPoolExecutor(max_workers=max_workers) as tpe:
      futures = [tpe.submit(self.scrape_article, link) for link in links]
      
      for future in futures:
        try:
          yield future.result()
        except SkipIteration:
          pass
    