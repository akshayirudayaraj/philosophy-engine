from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.models import Input, Output
from output import get_model_output_from_query

app = FastAPI(title="phil rag api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://philosophy-engine-q7xd-8kdjhwfuc-akshayirudayarajs-projects.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/query')
async def process_query(user_inp: Input) -> Output:
  query = user_inp.user_query
  docs, output = await get_model_output_from_query(query)
  
  return Output(
    related_documents=docs,
    model_output=output,
  )