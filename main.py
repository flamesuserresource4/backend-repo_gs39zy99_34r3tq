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


def seed_quotes_if_empty(tag: Optional[str] = None):
    # If collection is empty (optionally by tag), seed with a curated list of 120+ quotes
    count_filter = {}
    if tag:
        count_filter = {"tags": {"$in": [tag]}}
    existing = db["quote"].count_documents(count_filter)
    if existing > 0:
        return

    seeds: List[dict] = [
        {"text": "The only limit to our realization of tomorrow is our doubts of today.", "author": "Franklin D. Roosevelt", "tags": ["inspiration", "future"]},
        {"text": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt", "tags": ["confidence", "motivation"]},
        {"text": "Do what you can, with what you have, where you are.", "author": "Theodore Roosevelt", "tags": ["action"]},
        {"text": "It always seems impossible until it's done.", "author": "Nelson Mandela", "tags": ["perseverance"]},
        {"text": "Whether you think you can or you think you can't, you're right.", "author": "Henry Ford", "tags": ["mindset", "belief"]},
        {"text": "Act as if what you do makes a difference. It does.", "author": "William James", "tags": ["impact", "action"]},
        {"text": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill", "tags": ["success", "resilience"]},
        {"text": "What we think, we become.", "author": "Buddha", "tags": ["mindset"]},
        {"text": "Everything you can imagine is real.", "author": "Pablo Picasso", "tags": ["creativity"]},
        {"text": "Well done is better than well said.", "author": "Benjamin Franklin", "tags": ["action"]},
        {"text": "You must be the change you wish to see in the world.", "author": "Mahatma Gandhi", "tags": ["change", "leadership"]},
        {"text": "In the middle of difficulty lies opportunity.", "author": "Albert Einstein", "tags": ["opportunity", "resilience"]},
        {"text": "Happiness is not by chance, but by choice.", "author": "Jim Rohn", "tags": ["happiness", "choice"]},
        {"text": "Dream big and dare to fail.", "author": "Norman Vaughan", "tags": ["dreams", "risk"]},
        {"text": "The best way out is always through.", "author": "Robert Frost", "tags": ["perseverance"]},
        {"text": "If I cannot do great things, I can do small things in a great way.", "author": "Martin Luther King Jr.", "tags": ["excellence", "action"]},
        {"text": "If you're going through hell, keep going.", "author": "Winston Churchill", "tags": ["resilience"]},
        {"text": "You miss 100% of the shots you don't take.", "author": "Wayne Gretzky", "tags": ["action", "risk"]},
        {"text": "The future depends on what you do today.", "author": "Mahatma Gandhi", "tags": ["future", "action"]},
        {"text": "It does not matter how slowly you go as long as you do not stop.", "author": "Confucius", "tags": ["perseverance"]},
        {"text": "Everything you’ve ever wanted is on the other side of fear.", "author": "George Addair", "tags": ["courage", "fear"]},
        {"text": "Don’t watch the clock; do what it does. Keep going.", "author": "Sam Levenson", "tags": ["perseverance", "time"]},
        {"text": "The secret of getting ahead is getting started.", "author": "Mark Twain", "tags": ["action", "beginnings"]},
        {"text": "If opportunity doesn’t knock, build a door.", "author": "Milton Berle", "tags": ["opportunity", "initiative"]},
        {"text": "Perseverance is not a long race; it is many short races one after the other.", "author": "Walter Elliot", "tags": ["perseverance"]},
        {"text": "Quality is not an act, it is a habit.", "author": "Aristotle", "tags": ["excellence", "habits"]},
        {"text": "Strive not to be a success, but rather to be of value.", "author": "Albert Einstein", "tags": ["success", "value"]},
        {"text": "Try not to become a man of success, but rather try to become a man of value.", "author": "Albert Einstein", "tags": ["success", "value"]},
        {"text": "The best revenge is massive success.", "author": "Frank Sinatra", "tags": ["success", "motivation"]},
        {"text": "What you get by achieving your goals is not as important as what you become by achieving your goals.", "author": "Zig Ziglar", "tags": ["goals", "growth"]},
        {"text": "I am not a product of my circumstances. I am a product of my decisions.", "author": "Stephen R. Covey", "tags": ["choice", "mindset"]},
        {"text": "Setting goals is the first step in turning the invisible into the visible.", "author": "Tony Robbins", "tags": ["goals", "action"]},
        {"text": "If you can dream it, you can do it.", "author": "Walt Disney", "tags": ["dreams", "action"]},
        {"text": "I didn’t fail the test. I just found 100 ways to do it wrong.", "author": "Benjamin Franklin", "tags": ["learning", "failure"]},
        {"text": "Either you run the day, or the day runs you.", "author": "Jim Rohn", "tags": ["productivity", "habits"]},
        {"text": "The harder you work for something, the greater you’ll feel when you achieve it.", "author": "Unknown", "tags": ["work", "achievement"]},
        {"text": "Don’t limit your challenges. Challenge your limits.", "author": "Unknown", "tags": ["challenge", "growth"]},
        {"text": "Little by little, one travels far.", "author": "J.R.R. Tolkien", "tags": ["progress", "patience"]},
        {"text": "It’s not whether you get knocked down; it’s whether you get up.", "author": "Vince Lombardi", "tags": ["resilience"]},
        {"text": "You are never too old to set another goal or to dream a new dream.", "author": "C.S. Lewis", "tags": ["dreams", "goals"]},
        {"text": "Start where you are. Use what you have. Do what you can.", "author": "Arthur Ashe", "tags": ["action", "beginnings"]},
        {"text": "Aim for the moon. If you miss, you may hit a star.", "author": "W. Clement Stone", "tags": ["ambition", "optimism"]},
        {"text": "The way to get started is to quit talking and begin doing.", "author": "Walt Disney", "tags": ["action"]},
        {"text": "Opportunities don't happen. You create them.", "author": "Chris Grosser", "tags": ["opportunity", "initiative"]},
        {"text": "Don’t be pushed by your problems. Be led by your dreams.", "author": "Ralph Waldo Emerson", "tags": ["dreams", "mindset"]},
        {"text": "Go the extra mile. It’s never crowded there.", "author": "Wayne Dyer", "tags": ["excellence", "effort"]},
        {"text": "A year from now you may wish you had started today.", "author": "Karen Lamb", "tags": ["beginnings", "time"]},
        {"text": "Failure is simply the opportunity to begin again, this time more intelligently.", "author": "Henry Ford", "tags": ["failure", "learning"]},
        {"text": "You become what you believe.", "author": "Oprah Winfrey", "tags": ["belief", "mindset"]},
        {"text": "Courage is grace under pressure.", "author": "Ernest Hemingway", "tags": ["courage"]},
        {"text": "Action is the foundational key to all success.", "author": "Pablo Picasso", "tags": ["action", "success"]},
        {"text": "Turn your wounds into wisdom.", "author": "Oprah Winfrey", "tags": ["wisdom", "growth"]},
        {"text": "If you want to lift yourself up, lift up someone else.", "author": "Booker T. Washington", "tags": ["kindness", "leadership"]},
        {"text": "It’s not the load that breaks you down, it’s the way you carry it.", "author": "Lou Holtz", "tags": ["resilience", "mindset"]},
        {"text": "The man who moves a mountain begins by carrying away small stones.", "author": "Confucius", "tags": ["progress", "patience"]},
        {"text": "Do what is right, not what is easy nor what is popular.", "author": "Roy T. Bennett", "tags": ["integrity", "courage"]},
        {"text": "Doubt kills more dreams than failure ever will.", "author": "Suzy Kassem", "tags": ["fear", "mindset"]},
        {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs", "tags": ["work", "passion"]},
        {"text": "We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "author": "Will Durant", "tags": ["excellence", "habits"]},
        {"text": "If people are doubting how far you can go, go so far that you can’t hear them anymore.", "author": "Michele Ruiz", "tags": ["confidence", "focus"]},
        {"text": "Don’t wait for opportunity. Create it.", "author": "Unknown", "tags": ["opportunity", "initiative"]},
        {"text": "If you want to achieve greatness stop asking for permission.", "author": "Unknown", "tags": ["ambition", "courage"]},
        {"text": "I can and I will. Watch me.", "author": "Carrie Green", "tags": ["confidence", "determination"]},
        {"text": "Difficult roads often lead to beautiful destinations.", "author": "Unknown", "tags": ["perseverance", "optimism"]},
        {"text": "Great things are done by a series of small things brought together.", "author": "Vincent Van Gogh", "tags": ["progress", "craft"]},
        {"text": "Success usually comes to those who are too busy to be looking for it.", "author": "Henry David Thoreau", "tags": ["success", "work"]},
        {"text": "Do one thing every day that scares you.", "author": "Eleanor Roosevelt", "tags": ["courage", "growth"]},
        {"text": "If you’re offered a seat on a rocket ship, don’t ask what seat! Just get on.", "author": "Sheryl Sandberg", "tags": ["opportunity", "action"]},
        {"text": "If you want something you’ve never had, you must be willing to do something you’ve never done.", "author": "Thomas Jefferson", "tags": ["change", "risk"]},
        {"text": "Energy and persistence conquer all things.", "author": "Benjamin Franklin", "tags": ["energy", "perseverance"]},
        {"text": "Hardships often prepare ordinary people for an extraordinary destiny.", "author": "C.S. Lewis", "tags": ["resilience", "destiny"]},
        {"text": "Keep your eyes on the stars and your feet on the ground.", "author": "Theodore Roosevelt", "tags": ["ambition", "humility"]},
        {"text": "We can do anything we want to if we stick to it long enough.", "author": "Helen Keller", "tags": ["perseverance", "focus"]},
        {"text": "The only person you should try to be better than is the person you were yesterday.", "author": "Unknown", "tags": ["growth", "self"]},
        {"text": "I never lose. I either win or learn.", "author": "Nelson Mandela", "tags": ["learning", "mindset"]},
        {"text": "It always seems impossible until it’s done.", "author": "Nelson Mandela", "tags": ["perseverance"]},
        {"text": "Opportunities multiply as they are seized.", "author": "Sun Tzu", "tags": ["opportunity", "strategy"]},
        {"text": "Genius is 1% inspiration and 99% perspiration.", "author": "Thomas Edison", "tags": ["work", "innovation"]},
        {"text": "If you fell down yesterday, stand up today.", "author": "H.G. Wells", "tags": ["resilience"]},
        {"text": "Your big opportunity may be right where you are now.", "author": "Napoleon Hill", "tags": ["opportunity", "focus"]},
        {"text": "Keep going. Everything you need will come to you at the perfect time.", "author": "Unknown", "tags": ["patience", "perseverance"]},
        {"text": "The key to success is to start before you are ready.", "author": "Marie Forleo", "tags": ["action", "success"]},
        {"text": "Dreams don’t work unless you do.", "author": "John C. Maxwell", "tags": ["work", "dreams"]},
        {"text": "Stay hungry. Stay foolish.", "author": "Steve Jobs", "tags": ["curiosity", "growth"]},
        {"text": "Make each day your masterpiece.", "author": "John Wooden", "tags": ["excellence", "habits"]},
        {"text": "Do something today that your future self will thank you for.", "author": "Unknown", "tags": ["future", "habits"]},
        {"text": "If you get tired, learn to rest, not to quit.", "author": "Banksy", "tags": ["rest", "resilience"]},
        {"text": "Success is the sum of small efforts, repeated day in and day out.", "author": "Robert Collier", "tags": ["habits", "success"]},
        {"text": "You don’t have to be great to start, but you have to start to be great.", "author": "Zig Ziglar", "tags": ["beginnings", "growth"]},
        {"text": "Work hard in silence, let success make the noise.", "author": "Frank Ocean", "tags": ["work", "success"]},
        {"text": "Be so good they can’t ignore you.", "author": "Steve Martin", "tags": ["excellence", "craft"]},
        {"text": "Don’t stop until you’re proud.", "author": "Unknown", "tags": ["perseverance", "pride"]},
        {"text": "Focus on being productive instead of busy.", "author": "Tim Ferriss", "tags": ["productivity", "focus"]},
        {"text": "The best preparation for tomorrow is doing your best today.", "author": "H. Jackson Brown Jr.", "tags": ["excellence", "present"]},
        {"text": "The harder the conflict, the greater the triumph.", "author": "George Washington", "tags": ["resilience", "victory"]},
        {"text": "If you want to go fast, go alone. If you want to go far, go together.", "author": "African Proverb", "tags": ["teamwork", "leadership"]},
        {"text": "A goal is a dream with a deadline.", "author": "Napoleon Hill", "tags": ["goals", "planning"]},
        {"text": "Discipline is the bridge between goals and accomplishment.", "author": "Jim Rohn", "tags": ["discipline", "goals"]},
        {"text": "Success is walking from failure to failure with no loss of enthusiasm.", "author": "Winston Churchill", "tags": ["success", "resilience"]},
        {"text": "If you cannot do great things, do small things in a great way.", "author": "Napoleon Hill", "tags": ["excellence", "action"]},
        {"text": "The best time to plant a tree was 20 years ago. The second best time is now.", "author": "Chinese Proverb", "tags": ["time", "action"]},
        {"text": "Believe in yourself and all that you are.", "author": "Christian D. Larson", "tags": ["belief", "confidence"]},
        {"text": "The only place where success comes before work is in the dictionary.", "author": "Vidal Sassoon", "tags": ["work", "success"]},
        {"text": "You are what you do, not what you say you’ll do.", "author": "Carl Jung", "tags": ["action", "integrity"]},
        {"text": "Success is not in what you have, but who you are.", "author": "Bo Bennett", "tags": ["success", "character"]},
        {"text": "What lies behind us and what lies before us are tiny matters compared to what lies within us.", "author": "Ralph Waldo Emerson", "tags": ["inner", "strength"]},
        {"text": "If you can’t fly then run, if you can’t run then walk, if you can’t walk then crawl, but whatever you do you have to keep moving forward.", "author": "Martin Luther King Jr.", "tags": ["perseverance", "progress"]},
        {"text": "He who has a why to live can bear almost any how.", "author": "Friedrich Nietzsche", "tags": ["purpose", "resilience"]},
        {"text": "The only way out is through.", "author": "Robert Frost", "tags": ["perseverance"]},
        {"text": "What we fear of doing most is usually what we most need to do.", "author": "Ralph Waldo Emerson", "tags": ["courage", "fear"]},
        {"text": "If you don't like the road you're walking, start paving another one.", "author": "Dolly Parton", "tags": ["change", "action"]},
        {"text": "We become what we think about.", "author": "Earl Nightingale", "tags": ["mindset", "focus"]},
        {"text": "Great things never come from comfort zones.", "author": "Unknown", "tags": ["growth", "comfort"]},
        {"text": "Success is a journey, not a destination.", "author": "Arthur Ashe", "tags": ["success", "journey"]},
        {"text": "Your time is limited, don’t waste it living someone else’s life.", "author": "Steve Jobs", "tags": ["time", "authenticity"]},
        {"text": "If you want to be the best, you must be willing to do things that other people aren’t willing to do.", "author": "Michael Phelps", "tags": ["excellence", "work"]},
        {"text": "A river cuts through rock, not because of its power, but because of its persistence.", "author": "James N. Watkins", "tags": ["perseverance", "patience"]},
        {"text": "Success isn’t owned, it’s leased. And rent is due every day.", "author": "J.J. Watt", "tags": ["discipline", "success"]},
        {"text": "Be yourself; everyone else is already taken.", "author": "Oscar Wilde", "tags": ["authenticity"]},
        {"text": "You have power over your mind—not outside events. Realize this, and you will find strength.", "author": "Marcus Aurelius", "tags": ["stoicism", "mindset"]},
        {"text": "The obstacle is the way.", "author": "Marcus Aurelius", "tags": ["stoicism", "resilience"]},
        {"text": "Fortune favors the bold.", "author": "Virgil", "tags": ["courage", "action"]},
        {"text": "We are what we repeatedly do. Excellence, then, is not an act but a habit.", "author": "Aristotle", "tags": ["excellence", "habits"]},
        {"text": "To live is the rarest thing in the world. Most people exist, that is all.", "author": "Oscar Wilde", "tags": ["life", "mindfulness"]},
        {"text": "What you do speaks so loudly that I cannot hear what you say.", "author": "Ralph Waldo Emerson", "tags": ["integrity", "action"]},
        {"text": "If you want to live a happy life, tie it to a goal, not to people or things.", "author": "Albert Einstein", "tags": ["happiness", "goals"]},
        {"text": "Success is getting what you want. Happiness is wanting what you get.", "author": "Dale Carnegie", "tags": ["success", "happiness"]},
        {"text": "The purpose of our lives is to be happy.", "author": "Dalai Lama", "tags": ["happiness", "purpose"]},
        {"text": "The only impossible journey is the one you never begin.", "author": "Tony Robbins", "tags": ["action", "journey"]},
        {"text": "Not all those who wander are lost.", "author": "J.R.R. Tolkien", "tags": ["adventure", "journey"]},
        {"text": "The journey of a thousand miles begins with one step.", "author": "Lao Tzu", "tags": ["beginnings", "journey"]},
        {"text": "Life is what happens when you’re busy making other plans.", "author": "John Lennon", "tags": ["life", "mindfulness"]},
        {"text": "You only live once, but if you do it right, once is enough.", "author": "Mae West", "tags": ["life", "mindfulness"]},
        {"text": "Keep your face always toward the sunshine—and shadows will fall behind you.", "author": "Walt Whitman", "tags": ["optimism"]},
        {"text": "Believe and act as if it were impossible to fail.", "author": "Charles Kettering", "tags": ["belief", "action"]},
        {"text": "What we achieve inwardly will change outer reality.", "author": "Plutarch", "tags": ["mindset", "change"]},
        {"text": "If you judge people, you have no time to love them.", "author": "Mother Teresa", "tags": ["kindness", "love"]},
        {"text": "Do what you feel in your heart to be right, for you’ll be criticized anyway.", "author": "Eleanor Roosevelt", "tags": ["courage", "authenticity"]},
        {"text": "Keep moving forward.", "author": "Walt Disney", "tags": ["progress", "perseverance"]},
        {"text": "Success is never owned, it’s rented – and rent is due every day.", "author": "Rory Vaden", "tags": ["discipline", "success"]},
        {"text": "If you want light to come into your life, you need to stand where it is shining.", "author": "Guy Finley", "tags": ["mindset", "positivity"]},
        {"text": "A ship is safe in harbor, but that’s not what ships are for.", "author": "John A. Shedd", "tags": ["risk", "purpose"]},
        {"text": "The grass is greener where you water it.", "author": "Neil Barringham", "tags": ["focus", "habits"]}
    ]

    for s in seeds:
        try:
            create_document("quote", QuoteSchema(**s))
        except Exception:
            pass


@app.get("/api/quotes/random", response_model=dict)
def random_quote(tag: Optional[str] = Query(default=None, description="Filter by tag")):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Seed the database on first run to ensure a rich dataset
    seed_quotes_if_empty(tag)

    pipeline = []
    if tag:
        pipeline.append({"$match": {"tags": {"$in": [tag]}}})
    pipeline.append({"$sample": {"size": 1}})
    docs = list(db["quote"].aggregate(pipeline))

    if not docs:
        raise HTTPException(status_code=404, detail="No quotes available for the specified filter")

    return serialize_doc(docs[0])


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
