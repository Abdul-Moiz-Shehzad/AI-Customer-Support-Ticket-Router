import logging
import math
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from app.models import TicketState
from app.services.embeddings import (
    generate_embeddings_batch,
    generate_embedding_single,
    cosine_similarity
)

logger = logging.getLogger(__name__)

# Function to ensure NLTK resources
def ensure_nltk_resources():
    import nltk
    for resource in ['punkt', 'punkt_tab', 'stopwords', 'wordnet', 'omw-1.4']:
        try:
            if resource.startswith('punkt'):
                nltk.data.find(f'tokenizers/{resource}')
            else:
                nltk.data.find(f'corpora/{resource}')
        except LookupError:
            logger.info(f"Downloading NLTK resource: {resource}")
            try:
                nltk.download(resource, quiet=True)
            except Exception as e:
                logger.error(f"Failed to download NLTK resource {resource}: {e}")

# Preprocess helper
def preprocess_text(text: str) -> list:
    if not text:
        return []
    try:
        ensure_nltk_resources()
        tokens = word_tokenize(text.lower())
    except Exception:
        # Fallback if nltk fails
        tokens = re.findall(r'\w+', text.lower())
        
    lemmatizer = WordNetLemmatizer()
    try:
        stop_words = set(stopwords.words('english'))
    except Exception:
        stop_words = set()
        
    cleaned = []
    for token in tokens:
        if token.isalnum() and token not in stop_words:
            cleaned.append(lemmatizer.lemmatize(token))
    return cleaned

class BM25:
    def __init__(self, corpus: list, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avg_doc_length = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0
        
        # Document frequencies for all terms
        self.doc_frequencies = {}
        for doc in corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                self.doc_frequencies[term] = self.doc_frequencies.get(term, 0) + 1
                
        # Precompute IDF for terms in the corpus
        self.idf = {}
        for term, freq in self.doc_frequencies.items():
            # Standard BM25 IDF
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def get_score(self, doc: list, query: list) -> float:
        score = 0.0
        doc_len = len(doc)
        if doc_len == 0 or self.avg_doc_length == 0:
            return 0.0
            
        tf = {}
        for term in doc:
            tf[term] = tf.get(term, 0) + 1
            
        for term in query:
            if term not in tf:
                continue
            freq = tf[term]
            idf = self.idf.get(term, 0.0)
            
            numerator = freq * (self.k1 + 1.0)
            denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_length))
            score += idf * (numerator / denominator)
            
        return score

DUMMY_KB = {
    "Billing": [
        {
            "title": "Payment Failed",
            "content": (
                "If a payment fails, verify that your card details are correct, "
                "your bank has not declined the transaction, and sufficient funds "
                "are available. Retry after a few minutes."
            )
        },
        {
            "title": "Invoice Download",
            "content": (
                "Customers can download invoices by navigating to "
                "Settings > Billing > Invoices and selecting the desired invoice."
            )
        },
        {
            "title": "Duplicate Charge",
            "content": (
                "Duplicate charges may occur due to temporary payment authorization. "
                "If multiple successful charges appear after 24 hours, escalate to billing."
            )
        },
    ],

    "Technical": [
        {
            "title": "Application Not Loading",
            "content": (
                "Clear browser cache, disable extensions, and try another browser. "
                "If the issue persists, collect console logs before escalation."
            )
        },
        {
            "title": "API Timeout",
            "content": (
                "Check API status, verify request payload size, and retry with exponential backoff."
            )
        },
        {
            "title": "Premium Features Missing",
            "content": (
                "Log out and log back in. Premium features may take up to 15 minutes "
                "to synchronize after an upgrade."
            )
        },
    ],

    "Account": [
        {
            "title": "Password Reset",
            "content": (
                "Customers can reset their password using the 'Forgot Password' link "
                "on the login page."
            )
        },
        {
            "title": "Account Locked",
            "content": (
                "Accounts are temporarily locked after multiple failed login attempts. "
                "Wait 15 minutes or reset the password."
            )
        },
        {
            "title": "Email Change",
            "content": (
                "Users can update their registered email from "
                "Profile > Account Settings after verification."
            )
        },
    ],

    "Feature Request": [
        {
            "title": "Feature Requests",
            "content": (
                "Customer feature requests should be recorded and forwarded to the Product team. "
                "Do not promise delivery dates."
            )
        },
        {
            "title": "Dark Mode",
            "content": (
                "Dark mode has been requested by multiple users and is currently under review."
            )
        },
    ],

    "Bug Report": [
        {
            "title": "Known UI Issues",
            "content": (
                "Minor UI rendering issues may occur on older browsers. "
                "Recommend updating the browser before escalating."
            )
        },
        {
            "title": "Unexpected Error",
            "content": (
                "Collect screenshots, browser version, operating system, and reproduction steps "
                "before forwarding to engineering."
            )
        },
    ],

    "Refund": [
        {
            "title": "Refund Policy",
            "content": (
                "Refund requests made within 14 days of purchase are generally eligible "
                "if the customer has not exceeded usage limits."
            )
        },
        {
            "title": "Large Refund Requests",
            "content": (
                "Refund requests exceeding $500 must always be reviewed by a human support agent."
            )
        },
    ],

    "General Inquiry": [
        {
            "title": "Business Hours",
            "content": (
                "Customer support is available Monday through Friday, "
                "9:00 AM to 6:00 PM UTC."
            )
        },
        {
            "title": "Contact Support",
            "content": (
                "Customers can reach support through email or the in-app help center."
            )
        },
        {
            "title": "Subscription Plans",
            "content": (
                "The platform offers Free, Pro, and Enterprise plans with different "
                "storage and collaboration limits."
            )
        },
    ],

    "Security": [
        {
            "title": "Compromised Account",
            "content": (
                "If a customer reports unauthorized access, immediately escalate the ticket. "
                "Do not send automated troubleshooting instructions."
            )
        },
        {
            "title": "Suspicious Login",
            "content": (
                "Ask the customer to change their password and enable multi-factor authentication."
            )
        },
    ]
}

CATEGORY_MAPPING = {
    "billing": ["Billing", "Refund"],
    "technical": ["Technical", "Bug Report"],
    "bug": ["Bug Report", "Technical"],
    "feature": ["Feature Request"],
    "general": ["General Inquiry", "Account"],
    "security": ["Security"],
    "account": ["Account"]
}

def fallback_categorize(message: str) -> str:
    import re
    msg = (message or "").lower()
    words = set(re.findall(r'\w+', msg))
    if any(k in words for k in ["refund", "invoice", "charge", "billing", "payment", "subscribe", "cancel", "price"]):
        return "billing"
    elif any(k in words for k in ["security", "unauthorized", "compromise", "compromised", "hack", "suspicious", "abuse", "access"]):
        return "security"
    elif any(k in words for k in ["password", "login", "reset", "lock", "locked", "email", "profile", "account"]):
        return "account"
    elif any(k in words for k in ["error", "crash", "bug", "broken", "load", "database", "api", "integration", "fail"]):
        return "technical"
    elif any(k in words for k in ["feature", "request", "add", "enhance", "suggest", "update", "idea", "improvement"]):
        return "feature"
    else:
        return "general"

# Flatten the KB articles structure
KB_ARTICLES = []
for category, articles in DUMMY_KB.items():
    for article in articles:
        KB_ARTICLES.append({
            "category": category,
            "title": article["title"],
            "content": article["content"]
        })

# Precompute tokens for the articles
TOKENIZED_CORPUS = [
    preprocess_text(art["title"] + " " + art["content"])
    for art in KB_ARTICLES
]

bm25_index = BM25(TOKENIZED_CORPUS)

# Embedding models and helpers imported from app.services.embeddings

async def seed_kb_embeddings_if_empty():
    from app.services.database import kb_collection
    if kb_collection is None:
        logger.error("MongoDB collection is not initialized. Cannot seed KB embeddings.")
        return
        
    try:
        count = await kb_collection.count_documents({})
        if count > 0:
            logger.info("Knowledge base articles with embeddings already seeded.")
            return
            
        logger.info("Seeding knowledge base articles with embeddings into MongoDB...")
        texts = [f"Title: {art['title']}\nContent: {art['content']}" for art in KB_ARTICLES]
        
        try:
            embeddings = generate_embeddings_batch(texts)
        except Exception as e:
            logger.error(f"Failed to generate embeddings for seeding: {e}. Skipping database seeding.")
            return
            
        db_docs = []
        for i, art in enumerate(KB_ARTICLES):
            db_docs.append({
                "category": art["category"],
                "title": art["title"],
                "content": art["content"],
                "embedding": embeddings[i]
            })
            
        await kb_collection.insert_many(db_docs)
        logger.info(f"Successfully seeded {len(db_docs)} KB articles with embeddings into MongoDB.")
    except Exception as e:
        logger.error(f"Error seeding KB articles into MongoDB: {e}")

# cosine_similarity imported from app.services.embeddings

async def search_kb(message: str, category: str = None) -> str:
    if not category:
        category = fallback_categorize(message)
        
    from app.services.database import kb_collection
    
    # Check if we can do vector similarity lookup from MongoDB
    if kb_collection is not None:
        try:
            # 1. Generate query embedding
            query_embedding = generate_embedding_single(message)
            
            # 2. Get all articles with embeddings from MongoDB
            cursor = kb_collection.find({})
            db_articles = []
            async for doc in cursor:
                db_articles.append(doc)
                
            if db_articles:
                scored_articles = []
                message_lower = (message or "").lower()
                
                for art in db_articles:
                    doc_embedding = art.get("embedding")
                    if not doc_embedding:
                        continue
                    
                    # Compute similarity
                    sim_score = cosine_similarity(query_embedding, doc_embedding)
                    score = sim_score
                    
                    # 1. Boost score if categories match
                    is_category_match = False
                    if category:
                        cat_clean = category.strip().lower()
                        mapped_keys = CATEGORY_MAPPING.get(cat_clean, [cat_clean])
                        if any(m.lower() == art["category"].lower() for m in mapped_keys):
                            score += 0.3
                            is_category_match = True
                            
                    # 2. Boost score for direct title substring match
                    title_lower = art["title"].lower()
                    has_title_substring = False
                    if len(title_lower) > 3 and title_lower in message_lower:
                        score += 0.5
                        has_title_substring = True
                        
                    # We consider the article if similarity is > 0.1 OR category matches OR title substring matches
                    if sim_score > 0.1 or has_title_substring or is_category_match:
                        scored_articles.append((score, art))
                
                # Sort and take top matches
                scored_articles.sort(key=lambda x: x[0], reverse=True)
                unique_articles = []
                seen_titles = set()
                for _, art in scored_articles:
                    if art["title"] not in seen_titles:
                        seen_titles.add(art["title"])
                        unique_articles.append(art)
                        if len(unique_articles) >= 3:
                            break
                            
                if unique_articles:
                    return "\n".join(f"- **{art['title']}**: {art['content']}" for art in unique_articles)
        except Exception as e:
            logger.error(f"Error in MongoDB vector similarity search: {e}. Falling back to BM25 search.")
            
    # Legacy BM25 fallback search
    logger.info("Executing legacy BM25 token matching search...")
    query_tokens = preprocess_text(message)
    scored_articles = []
    message_lower = (message or "").lower()
    
    for i, art in enumerate(KB_ARTICLES):
        doc_tokens = TOKENIZED_CORPUS[i]
        bm25_score = bm25_index.get_score(doc_tokens, query_tokens)
        score = bm25_score
        
        is_category_match = False
        if category:
            cat_clean = category.strip().lower()
            mapped_keys = CATEGORY_MAPPING.get(cat_clean, [cat_clean])
            if any(m.lower() == art["category"].lower() for m in mapped_keys):
                score += 3.0
                is_category_match = True
                
        title_lower = art["title"].lower()
        has_title_substring = False
        if len(title_lower) > 3 and title_lower in message_lower:
            score += 10.0
            has_title_substring = True
            
        if bm25_score > 0.0 or has_title_substring or is_category_match:
            scored_articles.append((score, art))
            
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    unique_articles = []
    seen_titles = set()
    for _, art in scored_articles:
        if art["title"] not in seen_titles:
            seen_titles.add(art["title"])
            unique_articles.append(art)
            if len(unique_articles) >= 3:
                break
                
    if unique_articles:
        return "\n".join(f"- **{art['title']}**: {art['content']}" for art in unique_articles)
        
    # Final fallback if absolutely no matches
    if not category:
        category = fallback_categorize(message)
        
    cat_clean = category.strip().lower()
    mapped_keys = CATEGORY_MAPPING.get(cat_clean, ["General Inquiry"])
    
    fallback_articles = []
    for k in mapped_keys:
        for kb_key, articles in DUMMY_KB.items():
            if kb_key.lower() == k.lower():
                fallback_articles.extend(articles)
                break
                
    if not fallback_articles:
        fallback_articles = DUMMY_KB.get("General Inquiry", [])
        
    return "\n".join(f"- **{art['title']}**: {art['content']}" for art in fallback_articles[:3])

async def kb_lookup(state: TicketState) -> dict:
    kb_context = await search_kb(state.message, state.category)
    logger.info(f"Knowledge Base lookup found match of length: {len(kb_context)}")
    return {"kb_context": kb_context}
