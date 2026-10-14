import os

# import-time clients (ChatGoogleGenerativeAI) need a key; no network call happens at construction
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
