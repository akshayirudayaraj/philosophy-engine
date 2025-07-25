'''
  Currently doesn't work after some code refactoring
  
  TODO:
    - Modify Article object construction to use the Metadata instance variable
    - All JSON handling should come from the JsonHelper class
'''

from typing import cast
import requests
from bs4 import BeautifulSoup, Tag

import json
import os
import datetime
import string
from shared_types import Article, Section

from pylatexenc.latex2text import LatexNodes2Text

def fetch_url(link: str) -> BeautifulSoup:
  page = requests.get(link)
  soup = BeautifulSoup(page.content, "lxml")
  return soup

def get_dates(date_info: str, date_format: str) -> tuple[str, str | None]:
    date_parts = date_info.split(';')
    
    original_date = date_parts[0]
    original_date = datetime.datetime.strptime(original_date.removeprefix("First published "), date_format)
    original_date = original_date.isoformat()
    
    revision_date = date_parts[1] if len(date_parts) > 1 else None
    if revision_date:
      revision_date = datetime.datetime.strptime(revision_date.removeprefix(" substantive revision "), date_format)
      revision_date = revision_date.isoformat()
      
    return original_date, revision_date
  
def get_content_by_section(all_tags) -> list[Section]:
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
  
class SkipIteration(Exception):
  pass

def get_author_information(article_id: str) -> tuple[list[str], list[str]]:
  soup = fetch_url(f'https://plato.stanford.edu/cgi-bin/encyclopedia/archinfo.cgi?entry={article_id}')
  
  citation_tag = soup.find('pre')
  assert citation_tag is not None, "The citation link being looked at is seriously messed up"
  citation = citation_tag.get_text()
  
  segments = citation.removeprefix(f'@InCollection{{sep-{article_id},').split('},')
  
  authors_combined = segments[0].split('{')[-1]
  editors_combined = segments[3].split('{')[-1]
  
  authors_last_first = authors_combined.split(' and ')
  editors_full_name = editors_combined.split(' and ')
  
  authors_full_name = [" ".join(author.split(', ')[::-1]) for author in authors_last_first]
  
  return authors_full_name, editors_full_name

def find_required(soup, **kwargs) -> Tag:
  tag = soup.find(**kwargs)
  if not isinstance(tag, Tag):
    raise ValueError("Unable to find tag! Something's wrong with the document you're searching.")
  else:
    return tag

def extract_article_data(link: str) -> Article:
  soup = fetch_url(link)

  title = find_required(soup, name="h1").get_text()
  if (title == 'Document Retired'):
    raise SkipIteration()
  
  date_format = '%a %b %d, %Y'
  date_info = find_required(soup, id="pubinfo").get_text()
  original_date, revision_date = get_dates(date_info, date_format)
  
  preamble = find_required(soup, id="preamble").get_text()
  
  main_content = find_required(soup, id="main-text")
  all_tags = main_content.descendants # includes nested
  
  # TODO: clean up some duplicate phrases in all_tags
  
  section_contents = get_content_by_section(all_tags)
  
  # TODO: move title, preamble/summary to metadata
  section_contents.append({
    "header": list(title),
    "text": preamble,
  }) # this technically should come first, but order shouldn't matter here and this allows for cleaner code
  
  biblio_list = [entry.get_text().replace("\n", " ") for entry in find_required(soup, id="bibliography").find_all("li")]
  
  authors, editors = get_author_information(link.split('/')[-2])
  
  return {
    'id': "sep-" + title.lower().replace(' ', '-').replace('/', '-'),
    'title': title,
    'authors': authors,
    'editors': editors,
    'original_date': original_date,
    'revision_date': revision_date,
    'link': link,
    'content': section_contents,
    'bibliography': biblio_list,
  }
  
def get_all_post_links(soup: BeautifulSoup) -> list[str]:
  article_entries = find_required(soup, id="content").find_all("a")
  links = [entry['href'] for entry in article_entries] # type: ignore
  # print(*links, sep='\n')
  return links # type: ignore

def write_dict_to_json(dict: dict, filepath: str) -> None:
  with open(filepath + '.json', 'w') as file:
    json.dump(dict, file, indent=4, ensure_ascii=False)
      
def scrape_article_and_store(link: str):
  print("scraping " + link)
    
  article = extract_article_data(link)
  
  print("writing " + article['title'])
  
  filepath = os.path.join(os.getcwd(), 'sep', 'articles', article['id'])
  
  write_dict_to_json(cast(dict, article), filepath)
    
  print("finished writing " + article['title'] + "!\n")

def main():
  sep_chronological_entries = "https://plato.stanford.edu/published.html"
  main_soup = fetch_url(sep_chronological_entries)

  entries = get_all_post_links(main_soup)
  
  for i, link in enumerate(entries, 1):
    try:
      scrape_article_and_store(link)
    except SkipIteration:
      pass
    
    print(f'{i}/1852')
  
if __name__ == '__main__':
  main()