from collections.abc import Generator
import os
import datetime
import string
from typing import cast

from bs4 import Tag
from scraper import Scraper, SkipIteration
from shared_types import Article, Section

from pylatexenc.latex2text import LatexNodes2Text

class SepScraper(Scraper):
  def get_dates(self, date_info: str) -> dict[str, str | None]:
    DATE_FORMAT = '%a %b %d, %Y'

    date_parts = date_info.split(';')
    
    original_date = date_parts[0]
    original_date = datetime.datetime.strptime(original_date.removeprefix("First published "), DATE_FORMAT)
    original_date = original_date.isoformat()
    
    revision_date = date_parts[1] if len(date_parts) > 1 else None
    if revision_date:
      revision_date = datetime.datetime.strptime(revision_date.removeprefix(" substantive revision "), DATE_FORMAT)
      revision_date = revision_date.isoformat()
      
    return {
      'original_date': original_date,
      'revision_date': revision_date
    }
    
  def get_content_by_section(self, all_tags) -> list[Section]:
    section_contents = []
    running_header_nest_tree = []
    header_tags = ['h1', 'h2', 'h3', 'h4']
      
    for i in all_tags:
      if i.name in header_tags:
        # keep a running memory and prefix that running header history to the section metadata
        # lower values take out last value in running list, higher values append to running list
        
        # TODO: delete entries where this is a header that has its own text (why not empty?)
          # assumption right now: every header has some (valuable) paragraph text underneath it before the next header,
          # which isn't necessarily true
        
        # print(running_header_nest_tree)
        
        prev = i.find_previous(header_tags)
        
        curr_header_text = i.get_text().lstrip(string.digits + '.' + ' ')
        
        # TODO: make custom comparator for code clarity if i really wanna
        curr_header_value = int(i.name.removeprefix('h'))
        prev_header_value = int(prev.name.removeprefix('h')) if prev is not None else None
        
        # matches entry # in list to the header #
          # empty h2 entry in case of h1->h3 (people make mistakes)
        if prev_header_value is None:
          pass
        elif curr_header_value <= prev_header_value:
          while curr_header_value <= prev_header_value:
            running_header_nest_tree.pop()
            prev_header_value -= 1
        else:
          while curr_header_value > prev_header_value+1:
            running_header_nest_tree.append("")
            curr_header_value -= 1
            
        running_header_nest_tree.append(curr_header_text)
            
        section_contents.append({
          "header": running_header_nest_tree.copy(),
          "text": "",
        })
          
      else:
        if section_contents: # should always exist (headers always first) so this is for sanity
          section_contents[-1]["text"] += LatexNodes2Text().latex_to_text(i.get_text()).replace("\n", " ")

    '''
      latex conversion to natural language: https://pylatexenc.readthedocs.io/en/latest/latex2text/
        certain logic operators aren't handled like logical and/or/not (\\land, etc.) - satisfactory for now
        because some people use the synonymous \\wedge, etc.
        
        might want to find better conversion in the future
        
      how to handle logic formula trees??
    '''
    
    return section_contents

  def get_contributor_information(self, article_id: str) -> dict[str, list[str]]:
    soup = self._fetch_url(f'https://plato.stanford.edu/cgi-bin/encyclopedia/archinfo.cgi?entry={article_id}')
    
    citation_tag = soup.find('pre')
    assert citation_tag is not None, "the citation link being looked at is seriously messed up"
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
    soup = self._fetch_url(link)

    title = self.find_required(soup, name="h1").get_text()
    if (title == 'Document Retired'):
      raise SkipIteration()
    
    date_info = self.find_required(soup, id="pubinfo").get_text()
    dates = self.get_dates(date_info)
    
    preamble = self.find_required(soup, id="preamble").get_text()
    
    main_content = self.find_required(soup, id="main-text")
    all_tags = main_content.descendants # includes nested
    
    # TODO: clean up some duplicate phrases in all_tags
    
    section_contents = self.get_content_by_section(all_tags)
    
    biblio_list = [entry.get_text().replace("\n", " ") for entry in self.find_required(soup, id="bibliography").find_all("li")]
    
    sep_url_article_id = link.split('/')[-2]
    contributors = self.get_contributor_information(sep_url_article_id)
    
    return {
      'id': "sep-" + title.lower().replace(' ', '-').replace('/', '-'),
      'title': title,
      'content': section_contents,
      'metadata': {
        'authors': contributors['authors'],
        'editors': contributors['editors'],
        'original_date': cast(str, dates['original_date']), # hacky solution (i know original_date will always exist)
        'revised_date': dates['revision_date'],
        'link': link,
        'bibliography': biblio_list,
        'intro': preamble,
        'organization': 'Stanford Encyclopedia of Philosophy'
      },
    }
    
  def extract_links(self) -> Generator[str]:
    article_entries = self.find_required(self._beautiful_soup, id="content").find_all("a")
    for entry in article_entries:
      safe_entry = cast(Tag, entry) # lots of casts, too lazy rn to work around
      link = safe_entry.get('href')
      yield cast(str, link)
      
# def scrape_article_and_store(link: str):
#   print("scraping " + link)
    
#   article = extract_article_data(link)
  
#   print("writing " + article['title'])
  
#   filepath = os.path.join(os.getcwd(), 'sep', 'articles', article['id'])
  
#   JsonHelper.write_dict_to_json(cast(dict, article), filepath)
    
#   print("finished writing " + article['title'] + "!\n")

def main():
  sep_chronological_entries = "https://plato.stanford.edu/published.html"
  sep_scraper = SepScraper(base_scraping_url=sep_chronological_entries)
  
  article_directory = os.path.join('sep', 'articles')
  sep_scraper.scrape_and_store(base_write_directory=article_directory)
  # entries = get_all_post_links(main_soup)
  
  # for i, link in enumerate(entries, 1):
  #   try:
  #     scrape_article_and_store(link)
  #   except SkipIteration:
  #     pass
    
  #   print(f'{i}/1852')
  
if __name__ == '__main__':
  main()