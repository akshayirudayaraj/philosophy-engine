from collections.abc import Generator
import string
from typing import cast

from bs4 import Tag
import datetime
from pylatexenc.latex2text import LatexNodes2Text
import json

from core.storage.sqlite_helper import SqliteHelper, ArticleStorage
from core.scraping.scraper import _BaseScraper, SkipIteration, ParseException
from shared_types import Article, Section

# TODO: refactor class so it's more modular and functions aren't so tall
class SepScraper(_BaseScraper):
  DATE_FORMAT: str = '%a %b %d, %Y'
  _ACCEPTED_HEADER_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
  _ACCEPTED_TEXT_TAGS = ['p', 'blockquote', 'ol', 'ul', 'div']
  
  def __init__(self, base_scraping_url: str):
    super().__init__(base_scraping_url)
  
  def _get_dates(self, date_info: str) -> dict[str, str | None]:

    date_parts = date_info.split(';')
    
    original_date = date_parts[0]
    original_date = datetime.datetime.strptime(original_date.removeprefix("First published "), self.DATE_FORMAT)
    original_date = original_date.isoformat()
    
    revision_date = date_parts[1] if len(date_parts) > 1 else None
    if revision_date:
      revision_date = datetime.datetime.strptime(revision_date.removeprefix(" substantive revision "), self.DATE_FORMAT)
      revision_date = revision_date.isoformat()
      
    return {
      'original_date': original_date,
      'revision_date': revision_date
    }
    
  def _update_running_header_list(self, current_element: Tag, prev_header: Tag | None, running_header_nest_list: list[str]) -> None:
    """
    keep a running memory and prefix that running header history to the section metadata\n
    lower values take out last value in running list, higher values append to running list\n
    matches entry # in list to the header #\n
    - empty h2 entry in case of h1->h3 (people make mistakes)
    """
        
    if prev_header is not None:      
      curr_header_value = int(current_element.name.removeprefix('h'))
      prev_header_value = int(prev_header.name.removeprefix('h'))

      if current_element.name <= prev_header.name:
        while curr_header_value <= prev_header_value:
          running_header_nest_list.pop()
          prev_header_value -= 1
      else:
        while curr_header_value > prev_header_value+1:
          running_header_nest_list.append("")
          curr_header_value -= 1
    
    curr_header_text = current_element.get_text().lstrip(string.digits + '.' + ' ')
    running_header_nest_list.append(curr_header_text)
    
  def _extract_content_by_section(self, main_content: Tag) -> list[Section]:
    def add_content_to_last_section(text: str) -> None:
      # text = text.strip()
      text = LatexNodes2Text().latex_to_text(text)
      text = text.replace("\n", " ")
      section_contents[-1]['text'] += text
    
    content_children = main_content.children # tags and loose text, but no duplicates (as opposed to descendants)
      # PageElement is an abstract class (non exported), so it's important that this is here for type checking
      # each PageElement (what this iterates over) is either a Tag or NavigableString
        
    section_contents = []
    running_header_nest_list = []
      
    for current_element in content_children:
      if not isinstance(current_element, Tag): # then: NavigableString
        current_element = str(current_element)

        if current_element.strip() == '': # Empty string element; these happen often due to the way SEP formats HTML
          continue

        add_content_to_last_section(current_element)
      
      elif current_element.name in self._ACCEPTED_HEADER_TAGS:
          prev_child = current_element.find_previous(name=self._ACCEPTED_HEADER_TAGS)
          
          if not isinstance(prev_child, Tag | None):
            raise ParseException('prev_header current_element not a Tag or None')
            # there's no way this is an object other than a Tag because we're finding previous based on tag name
          
          self._update_running_header_list(current_element, prev_child, running_header_nest_list)
          
          if section_contents: # check this isn't first iteration
            # idea is that we do some trimming/cleaning operations when we know we're adding a new item to the list]
            if section_contents[-1]['text'] == "":
              section_contents.pop()
            else:
              section_contents[-1]['text'] = section_contents[-1]['text'].strip()

          section_contents.append({
            "header": running_header_nest_list.copy(),
            "text": "",
          })
          
      elif current_element.name in self._ACCEPTED_TEXT_TAGS:
        add_content_to_last_section(current_element.get_text())
        
      else:
        raise ParseException(f"Weird tag {current_element.name} unable to be processed. Direct current_element of main-text")

    '''
      latex conversion to natural language: https://pylatexenc.readthedocs.io/en/latest/latex2text/
        certain logic operators aren't handled like logical and/or/not (\\land, etc.) - satisfactory for now
        because some people use the synonymous \\wedge, etc.
        
        might want to find better conversion in the future
        
      TODO: how to handle logic formula lists??
    '''
    
    return section_contents

  def _get_contributor_information(self, article_id: str) -> dict[str, list[str]]:
    soup = self._fetch_url(f'https://plato.stanford.edu/cgi-bin/encyclopedia/archinfo.cgi?entry={article_id}')
    
    citation_tag = soup.find('pre')
    
    if not isinstance(citation_tag, Tag):
      raise ParseException("The <pre> tag for getting citations doesn't exist")
    
    citation = citation_tag.get_text()
    
    segments = citation.removeprefix(f'@InCollection{{sep-{article_id},').split('},')
    
    authors_combined = segments[0].split('{')[-1]
    editors_combined = segments[3].split('{')[-1]
    
    authors_last_first = authors_combined.split(' and ')
    editors_full_name = editors_combined.split(' and ')
    
    authors_full_name = [" ".join(author.split(', ')[::-1]) for author in authors_last_first]
    
    return {
      'authors': authors_full_name,
      'editors': editors_full_name
    }

  def scrape_article(self, link: str) -> Article:
    article_soup = self._fetch_url(link)

    title = self.find_required(article_soup, name="h1").get_text()
    if (title == 'Document Retired'):
      raise SkipIteration(title)
    
    date_info = self.find_required(article_soup, id="pubinfo").get_text()
    dates = self._get_dates(date_info)
    
    raw_preamble = self.find_required(article_soup, id="preamble").get_text()
    preamble = raw_preamble.replace("\n", " ").strip()
    
    main_content = self.find_required(article_soup, id="main-text")    
    section_contents = self._extract_content_by_section(main_content)
    
    biblio_list = [entry.get_text().replace("\n", " ") for entry in self.find_required(article_soup, id="bibliography").find_all("li")]
    
    sep_url_article_id = link.split('/')[-2]
    contributors = self._get_contributor_information(sep_url_article_id)
    authors = contributors['authors']
    editors = contributors['editors']
    
    return {
      'id': "sep-" + title.lower().replace(' ', '-').replace('/', '-'),
      'title': title,
      'content': section_contents,
      'metadata': {
        'authors': authors,
        'editors': editors,
        'original_date_published': cast(str, dates['original_date']), # hacky solution (current_element know original_date will always exist)
        'revision_date': dates['revision_date'],
        'link': link,
        'bibliography': biblio_list,
        'intro': preamble,
        'organization': 'Stanford Encyclopedia of Philosophy'
      },
    }
    
  def extract_links(self) -> Generator[str]:
    article_entries = self.find_required(id="content").find_all("a")
    for link_element in article_entries:
      if not isinstance(link_element, Tag):
        raise ParseException('A random NavigableString has made its way into the list of article entries')
      
      link = link_element.get('href')
      yield cast(str, link)

def main():
  sep_chronological_entries = "https://plato.stanford.edu/published.html"
  sep_scraper = SepScraper(base_scraping_url=sep_chronological_entries)
  
  sqlite_db_interface = SqliteHelper('sep.db')
  article_storage_helper = ArticleStorage(sqlite_db_interface)
  
  article_storage_helper.create_article_content_and_metadata_tables()
  
  data = sep_scraper.scrape_articles()
  
  article_storage_helper.store_article_dictionaries(data)
  
  # data = sep_scraper.scrape_article('https://plato.stanford.edu/entries/logic-games/')
  # print(json.dumps(data['content'], ensure_ascii=False, indent=4))
  
if __name__ == '__main__':
  main()