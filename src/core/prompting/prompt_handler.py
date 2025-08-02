from enum import Enum
import os
from typing import TypedDict
from anthropic import Anthropic

from core.file_helper import MdHelper, JsonHelper

class LargeLanguageModels(Enum):
  CLAUDE_HAIKU_3_5 = "claude-3-5-haiku-latest"
  CLAUDE_SONNET_4 = "claude-sonnet-4-latest"
  
class Prompt(TypedDict):
  system: str
  user: str
  thinking: str

class PromptHandler:
  WORDS_TO_TOKENS_APPROX = 1.3
  
  # TODO: eventually abstract into factory? once gpt-x, etc. are added
  def __init__(self, model_type: LargeLanguageModels, max_response_words: int = 5000):
    self.model_type = model_type
    self.max_tokens = int(max_response_words * self.WORDS_TO_TOKENS_APPROX)
    
    if model_type is LargeLanguageModels.CLAUDE_HAIKU_3_5 or LargeLanguageModels.CLAUDE_SONNET_4:
      self._client = Anthropic()
      
  def prompt_model(self, prompt: Prompt) -> None:
    response = self._client.messages.create(
      model=self.model_type.value,
      max_tokens=self.max_tokens,
      # thinking={
      #   'type': 'enabled',
      #   'budget_tokens': THINKING_TOKEN_BUDGET,
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
    
    MdHelper.write_to_md('claude_output', response.content[0].text)
    
  def get_prompt_context_from_vectors(self, results: dict) -> list[dict]:
    contextual_info = [self.get_text_from_vector(match) for match in results['matches']]

    return contextual_info

  def get_text_from_vector(self, match: dict) -> dict:
    id = match['id']
    link = match['metadata']['link']
    
    retrieval_title = match['metadata']['title']
    retrieval_headers = match['headers']
    
    internal_json_title = "sep-" + retrieval_title.lower() # .replace(' ', '-').replace('/', '-')
    
    article = JsonHelper.load_article(os.path.join('data', 'sep', 'articles', internal_json_title + '.json'))
    
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
  
  def construct_prompt(self, user_query: str, results: dict) -> Prompt:
    system_prompt = """
    You are a scholar of philosophy and ethics. Your mission is to help young philosopers and ethicists
    think about very hard, nuanced questions. Because you are wise, you offer many potential answers to questions
    and spend time in deliberation before reaching a conclusion. You never dismiss questions as merely "difficult" or "unclear" 
    - instead, you dissect complexity to reveal underlying structures and possibilities for meaningful engagement.
    
    Your scholarly approach involves:
    - Systematic examination of philosophical positions and their implications
    - Integration of diverse theoretical frameworks and methodological approaches  
    - Rigorous logical analysis that anticipates and addresses potential objections
    - Synthesis of ideas that builds toward novel insights while remaining grounded in established scholarship
    - Intellectual humility that acknowledges limitations while still advancing substantive conclusions
    """
    
    contextual_info = self.get_prompt_context_from_vectors(results)
    
    user_prompt = f"""
      <context>
      {[
        f"""
        <article>
        Title: {context['title']}
        Headers: {context['header_tree']}
        Text: {context['text']}
        </article>
        """
        for context in contextual_info
      ]}
      </context>
      
      <question>{user_query}</question>
      
      <analytical_framework>
      Your response must demonstrate advanced philosophical reasoning through the following required components:

      1. CONCEPTUAL ANALYSIS: Begin by unpacking key terms and concepts in the question. Identify ambiguities, define crucial terminology, and establish the philosophical stakes involved.

      2. THEORETICAL POSITIONING: Map the question within relevant philosophical traditions. Identify which schools of thought, historical figures, or contemporary debates this question intersects with.

      3. MULTI-PERSPECTIVE EXAMINATION: Present and analyze at least 3-4 distinct philosophical approaches to the question. For each perspective:
        - Articulate its core claims and underlying assumptions
        - Examine its strengths and explanatory power
        - Identify potential weaknesses or limitations
        - Consider how it might respond to objections

      4. CONTEXTUAL INTEGRATION: Weave the provided scholarly sources throughout your analysis. Demonstrate how these texts support, complicate, or extend different philosophical positions. Use direct quotations and specific references to show deep engagement with the material.

      5. CRITICAL SYNTHESIS: Develop your own reasoned position by:
        - Identifying points of convergence and tension between different approaches
        - Constructing novel arguments that build on existing scholarship
        - Addressing the strongest counterarguments to your position
        - Acknowledging areas where reasonable disagreement persists

      6. PHILOSOPHICAL IMPLICATIONS: Explore what your analysis reveals about broader questions in philosophy and ethics. Consider how your conclusions might apply to related problems or inform practical decision-making.
      </analytical_framework>

      <structural_requirements>
      Organize your essay with clear intellectual progression:

      - Introduction (300-400 words): Establish the philosophical significance of the question, preview your analytical approach, and outline your thesis
      - Conceptual Foundation (500-600 words): Provide necessary definitional and contextual groundwork
      - Comparative Analysis (1500-2000 words): Systematically examine multiple philosophical perspectives
      - Critical Evaluation (100-200 words): Develop and defend your own position through rigorous argumentation
      - Synthesis and Implications (100-200 words): Connect the analysis to broader philosophical questions and practical considerations

      Total target length: 2,500-3,400 words
      </structural_requirements>

      <scholarly_standards>
      - Use only complete sentences - this is an essay
      - Maintain academic rigor while remaining accessible to intelligent readers
      - Use precise philosophical terminology with appropriate explanation
      - Integrate citations naturally into your argumentation (aim for 8-12 substantial references to the provided sources)
      - Use MLA standard to reference citations - the citations should be at the ends of sentences, with the referenced article's title in parentheses
      - Demonstrate awareness of philosophical nuance and complexity
      - Show intellectual courage in defending positions while maintaining appropriate epistemic humility
      - Avoid hedging language that undermines substantive analysis ("this is complicated," "there are no easy answers")
      - Instead of claiming difficulty, demonstrate mastery by working through complexity systematically
      - Every sentence must be meaningful and unique, furthering the discussion in some way
      </scholarly_standards>

      <reasoning_depth_requirements>
      Your analysis must include:
      - At least two layers of objection and response (consider objections to your main arguments, then responses to those objections)
      - Examination of both theoretical and practical implications of different positions
      - Consideration of how the question connects to at least 2-3 other major philosophical problems
      - Discussion of methodological approaches (how different philosophical methods might yield different insights)
      - Integration of historical development of ideas with contemporary debates
      </reasoning_depth_requirements>
      
      <task>
      Write an in-depth, well-structured essay addressing the user's question. Use the context provided to structure
      your argumentation and frequently cite the articles you use in your essay. Be even-keeled and academic, and question
      your own logic as you draft the essay. Reason thoughtfully, thinking about all possible answers to the question.
      
      Provide an overview of how to approach the question and potential answers to it. Be nuanced, careful, and precise
      as you write. Use the scholarly texts provided as much as possible to outline and justify your arguments. Only use 
      complete sentences - this is an academic paper.
      </task>
    """
    
    thinking_prompt = """
    
    """
    
    return {
      'system': system_prompt,
      'user': user_prompt,
      'thinking': thinking_prompt
    }
    
class OutputException(Exception):
  pass