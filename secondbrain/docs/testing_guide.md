# Manual Testing Guide

## 1. System Startup
```bash
# Start your virtual environment (if not already active)
.\venv\Scripts\activate
```

## 2. API Startup
```bash
# Start the FastAPI server on port 8000
uvicorn api.chat:router --reload
```

## 3. MongoDB Startup
```bash
# Start MongoDB for conversation memory (port 27017)
docker run -d -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=admin --name mongodb mongo
```

## 4. Qdrant Startup
```bash
# Start Qdrant vector database (port 6333)
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant
```

---

## Manual Tests

### TEST 1: General Chat
* **Purpose**: Verify the router correctly identifies a non-RAG query and routes to the chat node.
* **Input**: `Hello`
* **Expected Graph Path**: Router ↓ Chat ↓ End
* **Expected Result**: A standard greeting response.
* **Expected Logs**: 
  * `NODE : ROUTER` -> Selected Route: `chat`
  * `NODE : CHAT` -> User Query: `Hello`
* **Expected Final Response**: "Hello! How can I assist you today?"

### TEST 2: RAG Query
* **Purpose**: Verify the end-to-end RAG pipeline executes correctly.
* **Input**: `What is this project about?`
* **Expected Graph Path**: Router ↓ Retrieve ↓ Grade ↓ Generate ↓ Verify ↓ End
* **Expected Result**: A grounded answer explaining the project based on the documents.
* **Expected Logs**: 
  * `NODE : ROUTER` -> Selected Route: `rag`
  * `NODE : RETRIEVE` -> Number of retrieved documents: > 0
  * `NODE : DOCUMENT GRADER` -> Pages that survived filtering
  * `NODE : GENERATE` -> Number of context documents
  * `NODE : HALLUCINATION CHECKER` -> Grounded: `True`
* **Expected Final Response**: A summary of the project.

### TEST 3: Conversation Memory
* **Purpose**: Verify MongoDB checkpointing remembers previous interactions in the same thread.
* **Request 1**: `"My name is Mandar"` (Thread: `mandar`)
* **Request 2**: `"What is my name?"` (Thread: `mandar`)
* **Expected Graph Path**: Router ↓ Chat ↓ End (for both requests)
* **Expected Result**: Assistant answers with "Mandar".
* **Expected Logs**: `Conversation Length: 4` (on the second request).
* **Expected Final Response**: "Your name is Mandar."

### TEST 4: Different Thread
* **Purpose**: Verify thread isolation in conversation memory.
* **Input**: `"What is my name?"` (Thread: `rahul`)
* **Expected Graph Path**: Router ↓ Chat ↓ End
* **Expected Result**: Assistant should NOT know the name.
* **Expected Logs**: `Conversation Length: 2`
* **Expected Final Response**: "I don't know your name yet."

### TEST 5: Query Rewrite
* **Purpose**: Trigger the query rewriter with an intentionally vague RAG query.
* **Input**: `"Tell me about the stuff in the document"`
* **Expected Graph Path**: Router ↓ Retrieve ↓ Grade ↓ Rewrite ↓ Retrieve ↓ Grade ↓ Generate ↓ Verify ↓ End
* **Expected Result**: The rewriter fires, generating a more specific query.
* **Expected Logs**:
  * `NODE : QUERY REWRITER`
  * Original Query: `Tell me about the stuff in the document`
  * Rewritten Query: `<A more specific search term>`
* **Expected Final Response**: Answer based on the rewritten query.

### TEST 6: Hallucination Check
* **Purpose**: Verify the hallucination checker catches ungrounded answers.
* **Input**: Ask something not present in the indexed PDF but using RAG keywords (e.g., `"Explain quantum physics according to the document"`).
* **Expected Graph Path**: Router ↓ Retrieve ↓ Grade ↓ Generate ↓ Verify ↓ Generate
* **Expected Result**: Grounded evaluates to False, printing the reason.
* **Expected Logs**:
  * `NODE : HALLUCINATION CHECKER`
  * Grounded: `False`
  * Reason: `<reason printed>`
* **Expected Final Response**: Model fallback or retry.

### TEST 7: Retriever
* **Purpose**: Verify vector retrieval pulls correct metadata.
* **Input**: Any RAG query.
* **Expected Graph Path**: Router ↓ Retrieve
* **Expected Result**: Documents are fetched from Qdrant.
* **Expected Logs**:
  * `NODE : RETRIEVE`
  * Number of retrieved documents: `5`
  * Page numbers: `['1', '4', ...]`
  * Source filenames: `['document.pdf', ...]`

### TEST 8: Document Grader
* **Purpose**: Verify the LLM correctly filters irrelevant documents.
* **Input**: A borderline RAG query.
* **Expected Graph Path**: Router ↓ Retrieve ↓ Grade
* **Expected Result**: Some retrieved documents are dropped before generation.
* **Expected Logs**:
  * `NODE : DOCUMENT GRADER`
  * Retrieved document count: `5`
  * Filtered document count: `< 5`

### TEST 9: Checkpoint
* **Purpose**: Verify the system state persists in MongoDB.
* **Input**: N/A
* **Expected Result**: MongoDB contains checkpoint documents.
* **Expected Logs**: Conversation survives multiple requests. You can inspect MongoDB using a tool like MongoDB Compass.

### TEST 10: Complete Flow
* **Purpose**: Run all flows sequentially to ensure no side-effects.
* **Run**: 
  1. `Hello`
  2. `What is this project about?`
  3. `What is my name?`
  4. `Explain quantum physics according to the project`
  5. `Tell me about the stuff`
* **Expected Result**: Verify the graph executes correctly without crashing or state corruption across all varied tests.
