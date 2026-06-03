import math
import requests
import numpy as np

STOPWORDS = {"what", "is", "the", "of", "and", "or", "to", "a", "an", "in", "on", "at", "by", "with", "your", "our", "my", "we", "you", "i", "do", "how", "where", "can", "why", "who", "whom", "this", "that", "these", "those", "for", "it", "its", "about", "me", "us", "they", "them", "he", "she", "his", "her", "him", "are", "was", "were", "be", "been", "have", "has", "had", "would", "should", "could", "will"}

def tokenize(text):
    if not text:
        return []
    # Lowercase and clean special characters
    clean = text.lower()
    for char in [".", ",", "!", "?", "\"", "(", ")", "'", "-", ";", ":", "/", "@"]:
        clean = clean.replace(char, " ")
    return [word for word in clean.split() if len(word) > 1 and word not in STOPWORDS]

class TFIDFSearchEngine:
    def __init__(self):
        self.documents = []
        self.vocabulary = set()
        self.idf = {}
        self.doc_vectors = []
        self.doc_norms = []

    def build_index(self, faq_items):
        self.documents = faq_items
        self.vocabulary = set()
        
        # Count document frequencies
        df = {}
        doc_tokens_list = []
        
        for item in faq_items:
            # Combine question, tags, and category to form rich indexing text
            text = f"{item['question']} {' '.join(item['tags'])} {item['category']}"
            tokens = tokenize(text)
            doc_tokens_list.append(tokens)
            
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1
                self.vocabulary.add(token)
                
        # Calculate IDF
        N = len(faq_items)
        for token, count in df.items():
            # Standard smooth IDF formula
            self.idf[token] = math.log(1 + N / (1 + count))
            
        # Calculate document TF-IDF vectors
        self.doc_vectors = []
        self.doc_norms = []
        for tokens in doc_tokens_list:
            vector = {}
            # Count Term Frequencies
            tf = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
                
            # Compute TF-IDF
            sum_squares = 0.0
            for token, freq in tf.items():
                tfidf_val = freq * self.idf.get(token, 0.0)
                vector[token] = tfidf_val
                sum_squares += tfidf_val ** 2
                
            self.doc_vectors.append(vector)
            self.doc_norms.append(math.sqrt(sum_squares))

    def search(self, query, top_k=3):
        if not self.documents:
            return []
            
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
            
        # Compute query vector
        query_tf = {}
        for token in query_tokens:
            query_tf[token] = query_tf.get(token, 0) + 1
            
        query_vector = {}
        sum_squares = 0.0
        for token, freq in query_tf.items():
            if token in self.idf:
                tfidf_val = freq * self.idf[token]
                query_vector[token] = tfidf_val
                sum_squares += tfidf_val ** 2
        
        query_norm = math.sqrt(sum_squares)
        if query_norm == 0:
            return []
            
        results = []
        for idx, doc_vector in enumerate(self.doc_vectors):
            doc_norm = self.doc_norms[idx]
            if doc_norm == 0:
                continue
                
            # Calculate Dot Product
            dot_product = 0.0
            for token, query_val in query_vector.items():
                if token in doc_vector:
                    dot_product += query_val * doc_vector[token]
                    
            similarity = dot_product / (query_norm * doc_norm)
            results.append({
                "document": self.documents[idx],
                "score": float(similarity)
            })
            
        # Sort by similarity score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class OllamaSearchEngine:
    def __init__(self, ollama_url="http://localhost:11434", model_name="nomic-embed-text"):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.documents = []
        self.embeddings = []

    def check_connection(self):
        try:
            # Quick check if Ollama is running by listing models or reading tag
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def get_embedding(self, text):
        payload = {
            "model": self.model_name,
            "input": text
        }
        response = requests.post(f"{self.ollama_url}/api/embed", json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Newer Ollama API returns embeddings in "embeddings" field
        if "embeddings" in data:
            return data["embeddings"][0]
        # Older api may return single embedding in "embedding"
        elif "embedding" in data:
            return data["embedding"]
        else:
            raise ValueError(f"Unexpected response format from Ollama embedding API: {data}")

    def build_index(self, faq_items):
        self.documents = faq_items
        self.embeddings = []
        
        if not self.check_connection():
            raise ConnectionError(f"Ollama server is not running or unreachable at {self.ollama_url}")
            
        print(f"Indexing FAQ base with Ollama '{self.model_name}' embeddings...")
        for item in faq_items:
            # Embed the question for matching
            text_to_embed = f"{item['question']} (tags: {', '.join(item['tags'])})"
            try:
                emb = self.get_embedding(text_to_embed)
                self.embeddings.append(emb)
            except Exception as e:
                print(f"Failed to embed item {item['id']}: {e}")
                # Fallback to zero vector or raise
                self.embeddings.append([0.0] * 768) # default size for nomic-embed-text
                
        self.embeddings = np.array(self.embeddings)

    def search(self, query, top_k=3):
        if not self.documents or len(self.embeddings) == 0:
            return []
            
        try:
            query_emb = np.array(self.get_embedding(query))
        except Exception as e:
            print(f"Ollama query embedding failed, falling back to TF-IDF. Error: {e}")
            return []
            
        # Cosine Similarity between query embedding and all documents
        dot_products = np.dot(self.embeddings, query_emb)
        doc_norms = np.linalg.norm(self.embeddings, axis=1)
        query_norm = np.linalg.norm(query_emb)
        
        # Handle zero divisions
        norms = doc_norms * query_norm
        norms[norms == 0] = 1e-9
        
        similarities = dot_products / norms
        
        results = []
        for idx, score in enumerate(similarities):
            results.append({
                "document": self.documents[idx],
                "score": float(score)
            })
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class RAGEngine:
    def __init__(self, mode="mock", ollama_url="http://localhost:11434", embedding_model="nomic-embed-text", llm_model="llama3"):
        self.mode = mode
        self.ollama_url = ollama_url
        self.llm_model = llm_model
        
        self.tfidf_engine = TFIDFSearchEngine()
        self.ollama_engine = OllamaSearchEngine(ollama_url, embedding_model)
        self.faq_items = []
        
    def initialize(self, faq_items):
        self.faq_items = faq_items
        # Always build TF-IDF index as it's the primary engine or backup
        self.tfidf_engine.build_index(faq_items)
        
        if self.mode == "ollama":
            try:
                self.ollama_engine.build_index(faq_items)
                print("Ollama embedding search index built successfully.")
            except Exception as e:
                print(f"Failed to build Ollama index ({e}). Falling back to TF-IDF mode.")
                self.mode = "mock"

    def search(self, query, top_k=3):
        if self.mode == "ollama":
            results = self.ollama_engine.search(query, top_k)
            # If Ollama fails and returns empty results, use TF-IDF fallback
            if not results:
                print("Ollama search failed/empty. Falling back to TF-IDF search.")
                return self.tfidf_engine.search(query, top_k)
            return results
        else:
            return self.tfidf_engine.search(query, top_k)

    def generate_answer(self, query, retrieved_results):
        # We need a similarity threshold below which we refuse to answer
        # The threshold depends on the search engine mode
        threshold = 0.35 if self.mode == "ollama" else 0.20
        
        if not retrieved_results or retrieved_results[0]["score"] < threshold:
            return {
                "answer": "I'm sorry, I couldn't find an answer to your question in our internal knowledge base. Can I help you with billing, shipping, account security, integrations, or partners instead?",
                "sources": [],
                "refused": True,
                "engine": self.mode,
                "confidence": 0.0 if not retrieved_results else retrieved_results[0]["score"]
            }
            
        # Extract top sources
        top_match = retrieved_results[0]["document"]
        confidence = retrieved_results[0]["score"]
        
        # If in Mock mode: return the exact FAQ answer wrapped nicely (simulating LLM)
        if self.mode == "mock":
            # Select relevant sources
            sources = [res["document"] for res in retrieved_results if res["score"] >= threshold]
            
            friendly_prefixes = [
                f"Based on our FAQ on **{top_match['question']}** under *{top_match['category']}*:",
                f"Regarding your query about {top_match['category']}, here is what I found in our documentation:",
                f"Here are the details from our database regarding *{top_match['question']}*:"
            ]
            # Simple rotation or hashing to select a prefix for variety
            prefix_idx = sum(ord(c) for c in query) % len(friendly_prefixes)
            answer_text = f"{friendly_prefixes[prefix_idx]}\n\n{top_match['answer']}\n\nIs there anything else I can help you with?"
            
            return {
                "answer": answer_text,
                "sources": sources,
                "refused": False,
                "engine": "mock",
                "confidence": confidence
            }
            
        # If in Ollama mode: call local LLM with prompt context
        elif self.mode == "ollama":
            sources = [res["document"] for res in retrieved_results if res["score"] >= threshold]
            
            # Format context
            context_blocks = []
            for i, res in enumerate(sources):
                doc = res["document"] if "document" in res else res
                context_blocks.append(f"Fact {i+1} [Category: {doc['category']}]:\nQuestion: {doc['question']}\nAnswer: {doc['answer']}")
            context_str = "\n\n".join(context_blocks)
            
            system_prompt = (
                "You are ShopGlide's helpful customer support chatbot.\n"
                "Your task is to answer the user's question using ONLY the facts provided in the Context below.\n"
                "If the answer is not contained in the provided facts, you MUST refuse to answer and say:\n"
                "'I'm sorry, I couldn't find an answer to your question in our internal knowledge base.'\n"
                "Be brief, professional, polite, and direct. Do not refer to the facts as 'Fact 1' or 'Context'. "
                "Synthesize them naturally as if you are the customer support assistant."
            )
            
            prompt = (
                f"Context facts:\n{context_str}\n\n"
                f"User Question: {query}\n\n"
                f"Agent Answer:"
            )
            
            try:
                payload = {
                    "model": self.llm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.2
                    }
                }
                
                response = requests.post(f"{self.ollama_url}/api/chat", json=payload, timeout=25)
                response.raise_for_status()
                response_data = response.json()
                answer_text = response_data["message"]["content"].strip()
                
                # Check if Ollama generated a refusal/cannot answer
                lower_ans = answer_text.lower()
                if "sorry" in lower_ans or "cannot find" in lower_ans or "not in the" in lower_ans or "don't know" in lower_ans or "couldn't find" in lower_ans:
                    # Double check if it matched the prompt instruction
                    return {
                        "answer": "I'm sorry, I couldn't find an answer to your question in our internal knowledge base. Can I help you with billing, shipping, account security, integrations, or partners instead?",
                        "sources": [],
                        "refused": True,
                        "engine": "ollama",
                        "confidence": confidence
                    }
                
                return {
                    "answer": answer_text,
                    "sources": sources,
                    "refused": False,
                    "engine": "ollama",
                    "confidence": confidence
                }
            except Exception as e:
                print(f"Ollama chat completion failed ({e}). Falling back to mock synthesis.")
                # Fallback to mock generation if Ollama fails
                self.mode = "mock"
                fallback_res = self.generate_answer(query, retrieved_results)
                # Reset mode to ollama
                self.mode = "ollama"
                return fallback_res
