from abc import ABC, abstractmethod
from enum import Enum
from typing import TypedDict

import os
from anthropic import Anthropic
from openai import OpenAI

from core.file_helper import MdHelper, JsonHelper

class LargeLanguageModels(Enum):
  CLAUDE_HAIKU_3_5 = "claude-3-5-haiku-latest"
  CLAUDE_SONNET_4 = "claude-sonnet-4-latest"
  GPT_5 = "gpt-5"
  O3 = "o3"
  
class Prompt(TypedDict):
  system: str
  user: str
  
class PromptHandlerFactory:
  @staticmethod
  def create_prompt_handler(model_type: LargeLanguageModels, max_response_words: int):
    match model_type:
      case LargeLanguageModels.CLAUDE_HAIKU_3_5 | LargeLanguageModels.CLAUDE_SONNET_4:
        return AnthropicPromptHandler(model_type=model_type, max_response_words=max_response_words)
      case LargeLanguageModels.GPT_5 | LargeLanguageModels.O3:
        return OpenAiPromptHandler(model_type=model_type, max_response_words=max_response_words)
      case _:
        raise ModelSelectionException()
  
class _PromptHandler(ABC):
  WORDS_TO_TOKENS_APPROX = 1.3

  def __init__(self, model_type: LargeLanguageModels, max_response_words: int):
    self.model_type = model_type
    self.max_tokens = int(max_response_words * self.WORDS_TO_TOKENS_APPROX)
    
  @abstractmethod
  def prompt_model(self, prompt: Prompt) -> None:
    pass
    
  def get_prompt_context_from_vectors(self, results: dict) -> list[dict]:
    contextual_info = [self.get_text_from_vector(match) for match in results]
    
    token_counter = 0
    for context in contextual_info:
      token_counter += len(context['text'].split(" ")) * self.WORDS_TO_TOKENS_APPROX 
    print(f'approx. context tokens {token_counter}')

    return contextual_info

  def get_text_from_vector(self, match: dict) -> dict:
    id = match['id']
    link = match['metadata']['link']
    
    retrieval_title = match['metadata']['title']
    retrieval_headers = match['metadata']['headers']
    
    internal_json_title = "sep-" + retrieval_title.lower().replace(' ', '-').replace('/', '-')
    
    article = JsonHelper.load_article(os.path.join('data', 'sep_v2', 'articles', internal_json_title + '.json'))
    
    content = self.find_header_text(article, retrieval_headers)
    
    print(f'id: {id}, link: {link}')
    print(content['text'] + '\n')
    
    return {
      'title': retrieval_title,
      'link': link,
      **content,
    }
    
  def find_header_text(self, article, retrieval_headers: list[str]) -> dict[str, str]:
    article_content = article['content']
    
    for section in article_content:
      if (section['header'] == retrieval_headers):
        return {
          'header_tree': ", ".join(section['header']),
          'text': section['text'],
        }
    
    # if can't find header, default is to get the context underneath the title
    return {
      'header_tree': article['title'],
      'text': article['metadata']['intro'],
    }
  
  def construct_prompt(self, user_query: str, results: dict) -> Prompt: # results are of type ScoredPineconeRecord
    system_prompt = """
    You are an AI assistant tasked with writing a comprehensive, academic-style paper on a philosophical or ethical question. 
    You will be provided with a set of high-quality, peer-reviewed research papers to help you answer the question. 
    Your goal is to produce a paper that philosophers and researchers might actually engage with and use in their research and to provide a comprehensive survey
    of perspectives to educate young philosophers.
    """
    
    contextual_info = self.get_prompt_context_from_vectors(results)
    
    user_prompt = f"""
      First, review the following research papers:
    
      <context>
      {[
        f"""
        <article>
        Title: {context['title']}
        Headers: {context['header_tree']}
        Text: {context['text']}
        Link: {context['link']}
        </article>
        """
        for context in contextual_info
      ]}
      </context>
      
      Now, consider the following philosophical question:
      
      <question>{user_query}</question>
      
      Your task is to write a comprehensive academic paper addressing this question. Before you begin writing, take some time to analyze the question and plan your approach. Do this work inside <paper_planning> tags in your thinking block:

      1. Analyze the question:
        - What are the key concepts involved?
        - What are the potential implications of this question?
        - How does this question relate to broader philosophical or ethical debates?

      2. Review the provided research papers:
        - What are the main arguments presented in each paper?
        - How do these papers relate to the question at hand?
        - Are there any conflicting viewpoints among the papers?
        - Identify and note down key quotes that support main points.

      3. Outline the paper structure:
        - Introduction
        - Conceptual Foundation
        - Comparative Analysis
        - Conclusion

      4. Plan the content for each section:
        - What key points should be addressed in each section?
        - What examples or evidence from the research papers can be used to support these points?
        - How can you ensure a logical flow of ideas throughout the paper?

      5. Consider potential challenges:
        - What are the main counterarguments to the positions you'll present?
        - How can you address these counterarguments effectively?
        - Plan how to incorporate these counterarguments and rebuttals into your paper.

      6. Reflect on clarity and accessibility:
        - How can you explain complex concepts in simple terms?
        - What jargon needs to be defined for the reader?
        - How can you use Markdown formatting to enhance readability?

      7. Prepare for the conclusion:
        - Based on your analysis, what do you believe is the most accurate answer to the question?
        - What are the key points that support this conclusion?
        - How can you address potential weaknesses in your argument?

      Now, write your academic paper using the following structure:

      1. Title: Use the question as the title of your paper.

      2. Introduction (150-400 words):
        - Explain how answering the question directly affects society.
        - Provide a one-sentence overview of the paper's structure.

      3. Conceptual Foundation (400-600 words):
        - Explain what each of the key terms mean.
        - Provide any relevant prerequisite information necessary to understand the question and its potential answers.
        - Define any jargon used, ensuring accessibility for readers.

      4. Comparative Analysis (1500-2500 words):
        - Explain different answers to the question.
        - Present the evidence supporting each of the different answers.
        - Delineate the key differences in principles that might lead one to favor one answer over another.
        - Be dynamic in how this section is structured, avoiding formulaic syntax.
        - Engage the reader with clear and varied writing and diction.
        - Mention specific philosophers and papers related to each perspective.
        - Use simple and clear language, avoiding overly long sentences.
        - Provide detailed reasoning behind every claim.

      5. Conclusion (500 words):
        - Present what you believe to be the most accurate, rational answer to the question.
        - If uncertain, state your uncertainties.
        - If confident in one perspective or a synthesis of perspectives, argue that position while maintaining logical consistency.
        - Reflect on potential counterarguments to your position.
        - Clearly distinguish between your own thoughts and those cited from others.

      Throughout your paper:

      - Use Markdown formatting for headers, subheaders, bold or italic text, subscripts, superscripts, special symbols, etc.
      - Use precise citations with parenthetical citations including the referenced article's title and link.
        Format the citations for Markdown, e.g., ([title](<link>))
      - Use the provided sources as evidence for each claim made.
      - When necessary or relevant, use deductive logic and symbols.
      - Be detailed and expressive, fully fleshing out each perspective discussed.

      Remember to treat this as a complete, peer-reviewed research paper. Exercise creative freedom in compiling the most extensive, comprehensive answer to the question while adhering to academic standards.

      Your final output should consist only of the academic paper, structured with appropriate headings for each section. Do not include any meta-commentary or notes about the writing process.

      Important reminders based on user feedback:
      1. Avoid using vague jargon or hyperspecific philosophical language without explanation. If you must use specialized terms, provide clear definitions or link to explanatory articles.
      2. Make extensive use of Markdown formatting. Use headers (##, ###) for main sections and subsections. Use bold (**text**) or italics (*text*) for emphasis or to highlight key points, rather than leaving fragmented sentences.
      3. Ensure you write a conclusion that presents and argues for your own perspective on the question, based on the evidence and arguments presented in the paper.

      Your final output should consist only of the academic paper and should not duplicate or rehash any of the work you did in the paper planning section.
    """
    
    print(f'total prompt tokens: {(len(system_prompt.split(" ")) + len(user_prompt.split(" "))) * self.WORDS_TO_TOKENS_APPROX}')
    
    return {
      'system': system_prompt,
      'user': user_prompt,
    }
  
  def write_to_output_file(self, response: str) -> None:
    MdHelper.write_to_md('model_output', response)
    
class AnthropicPromptHandler(_PromptHandler):
  # THINKING_TOKEN_BUDGET = 2000
  
  def __init__(self, model_type: LargeLanguageModels, max_response_words: int):
    super().__init__(model_type, max_response_words)
    self._client = Anthropic()
  
  def prompt_model(self, prompt: Prompt) -> None:
    response = self._client.messages.create(
      model=self.model_type.value,
      max_tokens=self.max_tokens,
      # thinking={
      #   'type': 'enabled',
      #   'budget_tokens': self.THINKING_TOKEN_BUDGET,
      # },
      system=[
        {
          'type': 'text',
          'text': prompt['system'],
          'cache_control': {'type': 'ephemeral'} # min cacheable prompt length: 1024 tokens
        }
      ],
      messages=[
        {
          'role': 'user',
          'content': prompt['user']
        }
      ],
    )
      
    if response.content[0].type != 'text':
      raise OutputException("the model output is not text for some strange reason")

    self.write_to_output_file(response.content[0].text)
    
# TODO: set up flex api (better pricing, higher latency)
class OpenAiPromptHandler(_PromptHandler):
  def __init__(self, model_type: LargeLanguageModels, max_response_words: int):
    super().__init__(model_type, max_response_words)
    self._client = OpenAI()
  
  def prompt_model(self, prompt: Prompt) -> None:
    if self.model_type.value[0].lower() == 'o': # reasoning series
      response = response = self._client.responses.create(
        model=self.model_type.value,
        max_output_tokens=self.max_tokens,
        instructions=prompt['system'],
        reasoning={
          'effort': 'medium',
          'summary': 'concise',
        },
        input=prompt['user']
      )
    else:
      response = self._client.responses.create(
        model=self.model_type.value,
        max_output_tokens=self.max_tokens,
        instructions=prompt['system'],
        input=prompt['user']
      )
    
    self.write_to_output_file(response.output_text)
  
class OutputException(Exception):
  pass

class ModelSelectionException(Exception):
  def __init__(self):
    print("Something's gone wrong with generating the prompt handler based on the model")
  pass