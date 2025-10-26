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
  
from typing import cast

from pydantic import BaseModel

from api.models import Document
from core.prompting.prompt_handler import OpenAILanguageModels, OpenAIPromptHandler, Prompt

class KnowledgeGraphEntry(BaseModel):
  subject: str
  verb: str
  obj: str
  
class KnowledgeGraph(BaseModel):
  entries: list[KnowledgeGraphEntry]
  
  def __str__(self):
    return "\n".join([f"{entry.subject}, {entry.verb}, {entry.obj}" for entry in self.entries])

# TODO: make entity/relationship extraction even more robust with NER/OpenIE
# TODO: potentially use SOTA out-of-the-box solution (Python library) kg-gen from Stanford
  # https://arxiv.org/pdf/2502.09956 
class KnowledgeGraphBuilder:  
  def __init__(self, user_query: str, documents_to_parse: list[Document], llm_for_generation: OpenAILanguageModels, kg_size_words: int = 1_500):
    self._user_query = user_query
    self._documents = documents_to_parse
    self._llm = llm_for_generation
    self._kg_size = kg_size_words
    
    self._prompt_handler = OpenAIPromptHandler(model_type=llm_for_generation, max_response_words=kg_size_words)
      # FIXME: rework prompt handler class (right now too hyperspecific to the RAG use-case e.g., the RAG prompt)
        
  async def generate_knowledge_graph(self) -> str:
    prompt = self._generate_kg_prompt()
    model_result = await self._prompt_handler.prompt_model_structured(
      prompt, 
      output_type=KnowledgeGraph,
      reasoning_level='low', # maybe move to typed dicts and pass in config dict (unwrap in function)
      text_verbosity='low',
    )
        
    kg = cast(KnowledgeGraph, model_result)
    str_kg = str(kg)
    
    return str_kg
  
  # potentially split into two LLM layers:
  # 1. source text -> structured entity extraction
  # 2. source text, structured entities -> SVO triplets
  # kg gen paper suggests this gives better results
  def _generate_kg_prompt(self) -> Prompt:
    system_prompt = """
    You are a linguist and philosophical analyst tasked with examining documents related to a specific philosophical question. 
    Your goal is to help another philosopher write an essay answering that question by generating a knowledge graph that delineates the relationships between concepts in the documents.
    """
    
    user_prompt = f"""
    The philosophical question you are examining is:
    <user_query>
    {self._user_query}
    </user_query>

    Here are the documents you need to review:
    <documents>
    {[
      f"""
      <document>
      Title: {doc.title}
      Headers: {doc.header_tree}
      Link: {doc.link}
      Text: {doc.text}
      </document>
      """
      for doc in self._documents
    ]}
    </documents>

    Your task is to create a knowledge graph in the form of Subject-Verb-Object (SVO) entries.
    Each entry should represent a relationship between concepts found in the documents.
    This will help the philosopher organize their thoughts in a more useful and correct way.

    To complete this task, follow these steps:

    1. Carefully review all the provided documents, paying attention to the titles and headers.

    2. As you review, identify a) key entities, concepts, and ideas, and b) relationships between those entities relevant to the user query.

    3. Create SVO entries that capture these relationships. Each entry should be on a new line and follow this format: "Subject-Verb-Object". For example: "Kant, supports, human rationality"
      - Keep in mind the context of the entire set of documents as you generate the relationships. You may generate multiple relationships for each subject but avoid lexical and semantic duplicates
  
    4. Use specific and meaning-packed verbs to accurately represent the relationships between subjects and objects.

    5. Before finalizing your list, plan out how you will draft your knowledge graph. Consider the following:
      - What are the main themes or concepts related to the user query?
      - How do these concepts relate to each other?
      - Are there any conflicting ideas or perspectives in the documents?
      - What hierarchies or categories can you identify among the concepts?

    6. After creating your initial list of SVO entries, review it carefully and refine it according to these guidelines:
      - Remove any duplicate entries or paraphrased relationships
      - Ensure each entry is unique and adds value to the knowledge graph
      - Check that the relationships accurately reflect the content of the documents
      - Verify that the entries are relevant to the user query

    7. Format your final output as a simple list of SVO entries, with each entry on a new line.

    Your final output should consist only of the SVO entries, without any additional explanation or commentary. Be concise and focus on providing a clear, comprehensive knowledge graph that will be useful for the philosopher writing the essay.    
    """
    
    return {
      'system': system_prompt,
      'user': user_prompt,
    }