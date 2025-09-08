# Phil: a philosophy RAG engine

## how to run it

deployment is WIP: frontend deployment on Vercel is finished; i'm currently working on deploying the backend to Render
right now, the best way to try this out is to run the project locally

1. [clone the repo](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
2. install the necessary libraries
    - while in the frontend directory: ```npm install```
    - while in the backend directory: ```pip install -r requirements.txt```
3. set up api keys / environment variables for: pinecone, openai, google vertex api
4. scrape->embed->upsert by executing the `pipeline.sh` file (this will take a while but it only has to be run once)
5. run the program by executing the `run.sh` file
6. visit localhost on your computer & enjoy!

some sample questions:

- does free will exist?
- to what extent, if any, should humans trust their senses?
- do objective moral truths exist?
- do people inherently deserve basic rights? if so, what should those rights be?

keep things open-ended! feel free to drift out of the scope of philosophy a bit as well

## how it works

preprocessing:

1. i scraped the text (includes title, headers+subheaders) and metadata (authors, editors, date published, etc.) from all entries in the Stanford Encyclopedia of Philosophy ([SEP](https://plato.stanford.edu/published.html))
2. sections of that text are then embedded as 1536-dimensional vectors using the [SOTA](https://huggingface.co/spaces/mteb/leaderboard) embedding model [`gemini-embedding-001`](https://ai.google.dev/gemini-api/docs/embeddings)
3. those embeddings along with relevant metadata (no raw article text to minimize cloud storage) are then upserted to the vector db ([pinecone](https://www.pinecone.io/))

when the user queries the engine:

1. the user query is embedded as a vector
2. the top-30 (adjustable) most semantically similar sources are retrieved (the 30 document vectors closest ([cosine similarity](https://www.pinecone.io/learn/vector-similarity/)) to the query vector)
3. those retrieved sources are then [reranked](https://huggingface.co/BAAI/bge-reranker-v2-m3) based on their textual context (as opposed to their condensed vector versions)
4. the most amount of sources that can fit in GPT-5's tier 1 TPM rate limit (30k) are then pulled and fed into the model along with my [prompt](https://github.com/akshayirudayaraj/philosophy-engine/blob/25629705e2e531578c4beeaa24f6db572d93261f/backend/src/core/prompting/prompt_handler.py#L145)
5. gpt-5 responds with a conceptual foundation, comparative analysis of different potential answers to the question (bulk of the response), and its own personal stance!

## what's next

1. more sources! bringing in contemporary papers from ethics, nous, etc. would make this model much more sophisticated and relevant for profs who want to understand the current stances on a variety of questions
2. add a middle layer [KG/mind mapping "agent"](https://arxiv.org/pdf/2502.04644) to help the LLM understand the relationships between complex topics before it responds

i welcome any and all feedback! please email me at akshay [dot] irudayaraj [at] gmail.com
