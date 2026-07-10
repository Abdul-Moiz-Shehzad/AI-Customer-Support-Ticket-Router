# AI Customer Support Ticket Router 🚀

An agentic, AI-powered customer support ticket categorization, prioritization, and routing system built for **TechEase Cloud**. This project uses an asynchronous, message-queue-driven architecture featuring a background worker running a multi-agent **LangGraph** workflow. It integrates **Google Gemini** for reasoning, **Sentence-Transformers** for dense semantic search/caching, **BM25** for sparse keyword lookup, and **RabbitMQ** for message distribution.

The repository is hosted at:  
👉 **[GitHub Repository](https://github.com/Abdul-Moiz-Shehzad/AI-Customer-Support-Ticket-Router)**

---

## 🗺️ System Architecture

The following diagram illustrates how customer support tickets flow through the system:

```mermaid
graph TD
    A[React Web App / Client] -->|1. Submit Ticket POST /classify| B(FastAPI API Server)
    B -->|2. Create 'pending' record| C[(MongoDB)]
    B -->|3. Publish Ticket Message| D[RabbitMQ: tickets_queue]
    
    subgraph Background Processing Worker
        E[aio-pika Consumer] <-->|4. Dequeue Message| D
        E -->|5. Check Message Cache| F(Semantic Cache)
        F -->|Hit| G[Save Completed Ticket]
        F -->|Miss| H[Invoke LangGraph Workflow]
        
        subgraph LangGraph Workflow
            H -->|Parallel Nodes| I[Categorize Node]
            H -->|Parallel Nodes| J[Prioritize Node]
            H -->|Parallel Nodes| K[KB Lookup Node]
            
            I & J & K -->|Fan-in Join| L[Context Buildup / Validation Node]
            
            L -->|Conditional Edge| M{Route Check}
            M -->|Escalation Required| N[User Queue Escalation]
            M -->|In-Domain & Answerable| O[Auto Reply Generator]
        end
        
        N & O -->|6. Save Final State| C
        N & O -->|7. Update Cache| F
    end

    G --> C
    A -->|8. Poll GET /ticket/:id| B
    B <-->|9. Read Results| C
```

---

## ✨ Key Features

- **Agentic LangGraph Workflow:** A resilient routing pipeline that concurrently processes ticket categorization, prioritization, and Knowledge Base lookup, followed by a validator node that makes routing decisions.
- **Hybrid Search Retrieval:** Combines sparse term-matching (**BM25** using NLTK preprocessing) with dense vector search (**Sentence-Transformers** cosine similarity on `all-MiniLM-L6-v2` embeddings) to retrieve contextually relevant knowledge base articles.
- **Semantic Caching:** Intercepts incoming messages to find semantically matching, historically processed tickets. If a highly similar query (cosine similarity > 0.85) is found, the system serves the cached response instantly, reducing API latency and LLM costs.
- **Asynchronous Processing:** Employs **RabbitMQ** via `aio-pika` to receive ticket payloads immediately, acknowledging them with a `queued` status while the background worker processes the agent workflow.
- **Interactive UI & Admin Dashboard:** A React application featuring a Customer Portal to submit tickets with real-time polling updates, and a Staff Dashboard to monitor live processed tickets, customer sentiments, priorities, routing departments, and responses.

---

## 🛠️ Technology Stack

### Backend
- **Core Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous API server)
- **Agent Orchestration:** [LangGraph](https://github.com/langchain-ai/langgraph) (Stateful multi-actor agent graph)
- **Large Language Models:** [LangChain Google GenAI](https://github.com/langchain-ai/langchain-google) (Powering `gemma-4-26b-a4b-it` and `gemini-3.1-flash-lite`)
- **Database Driver:** [Motor / PyMongo](https://motor.readthedocs.io/) (Asynchronous MongoDB client)
- **Message Broker client:** [aio-pika](https://aio-pika.readthedocs.io/) (Async RabbitMQ integration)
- **Natural Language Processing:** [NLTK](https://www.nltk.org/) (Text tokenization and lemmatization for BM25)
- **Dense Embeddings:** [Sentence-Transformers](https://sbert.net/) (`all-MiniLM-L6-v2` running locally via PyTorch)

### Frontend
- **Framework:** [React v19](https://react.dev/)
- **Routing:** [React Router DOM v7](https://reactrouter.com/)
- **Typing:** [TypeScript](https://www.typescriptlang.org/)
- **Styling:** Custom Vanilla CSS with modern dark gradients and clean dashboard layouts

---

## 📁 Repository Structure

```text
AI-Customer-Support-Ticket-Router/
├── backend/
│   ├── documentation/             # Project guides & tentative design layout
│   ├── src/
│   │   ├── app/
│   │   │   ├── routers/
│   │   │   │   └── process_ticket_router.py  # API endpoints
│   │   │   ├── services/
│   │   │   │   ├── categorize_ticket.py      # Category router node
│   │   │   │   ├── database.py               # MongoDB operations
│   │   │   │   ├── embeddings.py             # SentenceTransformers embedding generator
│   │   │   │   ├── graph_builder.py          # LangGraph structure & auto-reply validation
│   │   │   │   ├── kb_lookup.py              # Sparse BM25 + Dense Hybrid search engine
│   │   │   │   ├── prioritize_ticket.py      # Priority and sentiment analysis node
│   │   │   │   ├── process_ticket_service.py # Orchestrates cache lookup and graph execution
│   │   │   │   ├── rabbitmq_producer.py      # Publishes payload to queue
│   │   │   │   ├── semantic_cache.py         # Matcher/updater for semantic cache
│   │   │   │   └── database.py
│   │   │   ├── models.py                 # Pydantic state & IO model schemas
│   │   │   ├── main.py                   # FastAPI server initialization & startup events
│   │   │   └── worker.py                 # RabbitMQ background worker process
│   │   ├── utils/
│   │   │   └── config.py                 # LLM Model configurations
│   │   └── setup.py                      # Local editable install script
│   ├── .env                              # Environment configuration (ignored in git)
│   ├── requirements.txt                  # Python dependencies
│   └── .gitignore
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── landing.tsx               # Homepage / portal router
│   │   │   ├── tickets.tsx               # Ticket submission form with status polling
│   │   │   ├── dashboard.tsx             # Staff tickets grid and analytical summary view
│   │   │   └── notFound.tsx
│   │   ├── App.js                        # Client routes setup
│   │   ├── index.js                      # Entry point
│   │   └── index.css                     # Design tokens & core styles
│   ├── tsconfig.json                     # TypeScript compilation config
│   ├── package.json                      # Node packages & scripts
│   └── .gitignore
└── README.md                             # You are here
```

---

## ⚡ Setup & Installation

### 1. Prerequisites
Ensure you have the following services running locally:
- **MongoDB:** running on `mongodb://localhost:27017`
- **RabbitMQ:** running on `amqp://guest:guest@localhost:5672/`

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies and local modules:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend/` root directory:
   ```env
   GOOGLE_API_KEY="your-google-gemini-api-key-here"
   MONGO_URI="mongodb://localhost:27017"
   MONGO_DB="ticket_router_db"
   RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
   ```
5. Run the FastAPI application:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. In a **new terminal tab** (with environment activated), run the background queue worker:
   ```bash
   python src/app/worker.py
   ```

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the React development server:
   ```bash
   npm start
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 🔌 API Endpoints

### 📩 Submit Support Ticket
- **Endpoint:** `POST /classify`
- **Request Body:**
  ```json
  {
    "customer_name": "Jane Doe",
    "customer_email": "jane@example.com",
    "subscription": "Enterprise",
    "message": "I forgot my account password, how can I trigger a secure password reset?"
  }
  ```
- **Response:**
  ```json
  {
    "ticket_id": "c138b556-9a29-4700-84cf-233bbd4484bc",
    "status": "queued",
    "message": "Ticket submitted successfully and is being processed in the background."
  }
  ```

### 🔍 Get Ticket Status & Resolution
- **Endpoint:** `GET /ticket/{ticket_id}`
- **Response (Completed with Auto-Reply):**
  ```json
  {
    "ticket_id": "c138b556-9a29-4700-84cf-233bbd4484bc",
    "status": "completed",
    "category": "Account",
    "priority": "Medium",
    "department": "Support",
    "escalation_required": false,
    "reply_message": "Hello Jane Doe,\n\nTo reset your password, click on 'Forgot Password' on the login page and follow the link sent to your registered email address.\n\nSupport Team",
    "auto_reply_sent": true
  }
  ```

### 📊 Get All Tickets
- **Endpoint:** `GET /tickets`
- **Response:** Returns an array of all tickets in the MongoDB collection, sorted newest first.

---

## 🧠 Core Agent Workflow Logic

The **LangGraph** workflow operates on a strict routing logic after executing the concurrent categorization, prioritization, and KB lookup tasks:

1. **In-Domain Check:** Validates whether the ticket concerns TechEase Cloud's ecosystem (Cloud Storage, Collaboration, Billing, Accounts, API Platform).
   - *If Out-of-Domain:* The system instantly responds with a pre-configured template outlining support services and finishes the ticket (no human escalation).
2. **Context Sufficiency Check:** Determines if the compiled Knowledge Base context holds enough details to answer the query.
   - *If Context is insufficient:* Routes to the corresponding support department queue (`escalation_required = true`).
3. **Draft Drafting & ESC-Escalation:** If in-domain and context-sufficient, an auto-reply is drafted using Gemini.
   - If the LLM determines that the context is insufficient during drafting, it returns `[ESC]`, triggers an escalation, and routes the ticket to a human department queue.
4. **Auto-Escalation Rules:** Tickets are automatically routed to human queues (`escalation_required = true`) if:
   - The ticket priority is marked **High** (critical faults/billing refunds).
   - The customer sentiment is detected as **negative** (frustrated/angry clients).
   - The customer is on a **Premium** or **Enterprise** tier subscription.

---

## 🤝 Contribution

Contributions are welcome! Feel free to open issues or submit pull requests. For major architectural changes, please open an issue first to discuss your ideas.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---