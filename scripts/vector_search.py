import os
from pymongo import MongoClient
from dotenv import load_dotenv
import google.generativeai as genai # Reverted import back to google.generativeai

# Load environment variables at the beginning
load_dotenv()

# Configure the Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set. Gemini embeddings will not work.")
    # In a real application, you might want to raise an exception or handle this more gracefully
    # For now, we'll just exit if the key is critical for the script's function.
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

def get_embedding(text: str):
    """
    Generates a real Gemini embedding for the given text.
    """
    try:
        # Using the full model name 'models/gemini-embedding-001'
        response = genai.embed_content(model="models/gemini-embedding-001", content=[text])
        # The embedding vector is usually under the 'embedding' key, and it's a list of floats.
        return response['embedding'][0]
    except Exception as e:
        print(f"Error generating embedding for text: '{text[:50]}...': {e}")
        return None

def search_knowledge_base(query: str, limit: int = 5):
    """
    Performs a vector search on the product_knowledge_base collection.

    Args:
        query (str): The search query string.
        limit (int): The maximum number of results to return.

    Returns:
        list: A list of dictionaries, where each dictionary represents a matching document.
    """
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MONGODB_URI environment variable not set.")
        return []

    client = MongoClient(mongodb_uri)
    db = client.cofounder
    collection = db.product_knowledge_base

    query_embedding = get_embedding(query)
    if query_embedding is None:
        client.close()
        return []

    print(f"Searching knowledge base for query: '{query}' with limit {limit}...")

    try:
        # Atlas Vector Search aggregation pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "product_knowledge_base_vector_index", # Name of the vector search index
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 100, # Number of nearest neighbors to consider
                    "limit": limit # Number of results to return
                }
            },
            {
                "$project": {
                    "_id": 0, # Exclude the _id field
                    "content": 1,
                    "source_file": 1,
                    "score": { "$meta": "vectorSearchScore" } # Include the search score
                }
            }
        ]

        results = list(collection.aggregate(pipeline))
        print(f"Found {len(results)} results for query '{query}'.")
        return results

    except Exception as e:
        print(f"Error during vector search: {e}")
        return []
    finally:
        client.close()

if __name__ == "__main__":
    # Example usage:
    test_query = "B2B SaaS validation"
    search_results = search_knowledge_base(test_query, limit=3)

    if search_results:
        print("\nSearch Results:")
        for i, result in enumerate(search_results):
            print(f"--- Result {i+1} (Score: {result.get('score'):.4f}) ---")
            print(f"Source: {result.get('source_file')}")
            print(f"Content: {result.get('content')[:200]}...") # Print first 200 chars of content
            print("-" * 20)
    else:
        print("No results found for the query.")

    test_query_2 = "how to conduct customer interviews"
    search_results_2 = search_knowledge_base(test_query_2, limit=2)
    if search_results_2:
        print("\nSearch Results for second query:")
        for i, result in enumerate(search_results_2):
            print(f"--- Result {i+1} (Score: {result.get('score'):.4f}) ---")
            print(f"Source: {result.get('source_file')}")
            print(f"Content: {result.get('content')[:200]}...")
            print("-" * 20)
    else:
        print("No results found for the second query.")
