npm run dev --prefix frontend &
cd backend && uvicorn src.api.routes:app --reload &
wait