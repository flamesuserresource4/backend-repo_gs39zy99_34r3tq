import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Quote as QuoteSchema

app = FastAPI(title="Quotes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuoteCreate(BaseModel):
    text: str
    author: Optional[str] = "Unknown"
    tags: Optional[List[str]] = []
    template: Optional[str] = None


def serialize_doc(doc):
    d = dict(doc)
    if d.get("_id"):
        d["id"] = str(d.pop("_id"))
    # Convert datetime objects to isoformat
    for key in list(d.keys()):
        if hasattr(d[key], "isoformat"):
            d[key] = d[key].isoformat()
    return d


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Quotes Endpoints

@app.post("/api/quotes", response_model=dict)
def create_quote(payload: QuoteCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    quote = QuoteSchema(**payload.model_dump())
    inserted_id = create_document("quote", quote)
    return {"id": inserted_id}


@app.get("/api/quotes", response_model=List[dict])
def list_quotes(tag: Optional[str] = Query(default=None, description="Filter by tag"), limit: int = Query(default=50, ge=1, le=200)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_dict = {}
    if tag:
        filter_dict = {"tags": {"$in": [tag]}}
    docs = get_documents("quote", filter_dict, limit)
    return [serialize_doc(d) for d in docs]


@app.get("/api/quotes/random", response_model=dict)
def random_quote(tag: Optional[str] = Query(default=None, description="Filter by tag")):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    pipeline = []
    if tag:
        pipeline.append({"$match": {"tags": {"$in": [tag]}}})
    pipeline.append({"$sample": {"size": 1}})
    docs = list(db["quote"].aggregate(pipeline))

    # Seed with a few quotes if none exist
    if not docs:
        seeds = [
            {"text": "The only limit to our realization of tomorrow is our doubts of today.", "author": "Franklin D. Roosevelt", "tags": ["inspiration", "future"]},
            {"text": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt", "tags": ["confidence", "motivation"]},
            {"text": "Do what you can, with what you have, where you are.", "author": "Theodore Roosevelt", "tags": ["action"]},
            {"text": "It always seems impossible until it's done.", "author": "Nelson Mandela", "tags": ["perseverance"]},
        ]
        for s in seeds:
            create_document("quote", QuoteSchema(**s))
        docs = list(db["quote"].aggregate(pipeline)) or list(db["quote"].aggregate([{ "$sample": {"size": 1}}]))

    if not docs:
        raise HTTPException(status_code=404, detail="No quotes available")

    return serialize_doc(docs[0])


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
