from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

from api.models import Input, Output
from output import get_model_output_from_query

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="phil rag api")
app.state.limiter = limiter

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000", "https://philosophy-engine.vercel.app"],
  allow_origin_regex=r"^https://philosophy-engine[^.]*\.vercel\.app$",
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
  return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})

@app.post('/query')
@limiter.limit("5/minute")
async def process_query(request: Request, user_inp: Input) -> Output:
  query = user_inp.user_query
  docs, output = await get_model_output_from_query(query)
  
  return Output(
    related_documents=docs,
    model_output=output,
  )