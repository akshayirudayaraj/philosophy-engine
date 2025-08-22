# 1. get relevant context & documents
  # TODO: maybe get more than what's actually fed into the model for more comprehensive KG
  # (risks model getting confused if they see something without strong citations in context)
# 2. generate knowledge graph representing the entities and relationships between entities in the documents
  # Use Subject-Verb-Object (SVO) format e.g., (Kant, defends, Human Rationality)
  # Chunk context & batch prompt gpt-5-mini and use OpenAI's Structured Outputs (via Pydantic)
    # effort: minimal for good instruction-following but encourage the model to think in the prompt (https://platform.openai.com/docs/guides/latest-model)
      # increase to low if needed
  # Keep length overall low in general, maybe around 1.5-2k tokens max (not truncate but in prompting instructions)
# 3. pass in knowledge graph to prompt
  # dynamically adjust context length based on KG length
      
# prompt details
  # Explicitly ask for only unique triples (e.g., “Do not list duplicates or paraphrased relationships.”)
  # Require canonicalized entities, possibly with deduplication instructions.
  # Specify low verbosity and structured output.
  
from pydantic import BaseModel

from api.models import Document
from core.prompting.prompt_handler import LargeLanguageModels, Prompt, PromptHandlerFactory

class KnowledgeGraphEntry(BaseModel):
  subject: str
  verb: str
  obj: str

# TODO: make entity/relationship extraction even more robust with NER/OpenIE
# TODO: potentially use SOTA out-of-the-box solution (Python library) kg-gen from Stanford
  # https://arxiv.org/pdf/2502.09956 
class KnowledgeGraph:
  KG_MAX_SIZE = 1_500
  
  def __init__(self, documents_to_parse: list[Document], llm_for_generation: LargeLanguageModels):
    self._documents = documents_to_parse
    self._llm = llm_for_generation
    self._prompt_handler = PromptHandlerFactory.create_prompt_handler(model_type=llm_for_generation, max_response_words=self.KG_MAX_SIZE)
      # FIXME: rework prompt handler class (right now too hyperspecific to the RAG use-case e.g., the RAG prompt)
    
    self._kg_text = self.generate_knowledge_graph()
    
  async def generate_knowledge_graph(self) -> str:
    prompt = self._generate_kg_prompt()
    model_result = await self._prompt_handler.prompt_model(
      prompt, 
      config={
        'reasoning': {
          'effort': 'low', # 'minimal',
        },
        # 'text': {
        #   'verbosity': 'low',
        # },
        'text_format': list[KnowledgeGraphEntry]
      },
    )
    return model_result
    
  def _generate_kg_prompt(self) -> Prompt:
    # TODO: draft prompt and improve it with tools on https://console.anthropic.com/dashboard
    system_prompt = """
    
    """
    
    user_prompt = """
    
    
    """
    
    return {
      'system': system_prompt,
      'user': user_prompt,
    }