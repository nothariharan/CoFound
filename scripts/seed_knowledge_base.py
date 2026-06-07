import os
from pymongo import MongoClient
import glob
from dotenv import load_dotenv
import google.generativeai as genai
import time # Import the time module

# Load environment variables at the beginning
load_dotenv()

# Configure the Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set. Gemini embeddings will not work.")
    exit(1) # Exit if the API key is critical

genai.configure(api_key=GOOGLE_API_KEY)

_models_listed = False # Flag to ensure models are listed only once

def get_embedding(text: str):
    """
    Generates a real Gemini embedding for the given text.
    """
    global _models_listed # Declare intent to modify global variable
    try:
        # Using the full model name 'models/gemini-embedding-001'
        response = genai.embed_content(model="models/gemini-embedding-001", content=[text])
        # The embedding vector is usually under the 'embedding' key, and it's a list of floats.
        return response['embedding'][0]
    except Exception as e:
        print(f"Error generating embedding for text: '{text[:50]}...': {e}")
        if not _models_listed:
            print("Attempting to list available models (once)...")
            try:
                for m in genai.list_models():
                    if "embedContent" in m.supported_generation_methods:
                        print(f"Available embedding model: {m.name}")
            except Exception as list_e:
                print(f"Error listing models: {list_e}")
            _models_listed = True # Set flag to true after listing
        return None # Return None to indicate failure

def seed_knowledge_base():
    # MongoDB URI is also needed
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MONGODB_URI environment variable not set.")
        exit(1)

    client = MongoClient(mongodb_uri)
    db = client.cofounder
    collection = db.product_knowledge_base

    print("Seeding product_knowledge_base collection with framework documents...")

    docs_path = os.path.join(os.path.dirname(__file__), "..", "docs")
    markdown_files = glob.glob(os.path.join(docs_path, "**", "*.md"), recursive=True)

    if not markdown_files:
        print(f"No markdown files found in {docs_path}. Exiting.")
        client.close()
        return

    documents_to_insert = []
    for file_path in markdown_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Basic chunking: split by double newline for paragraphs.
            # This is a simple approach to get multiple chunks.
            chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]

            if not chunks:
                print(f"No processable content chunks found in {file_path}. Skipping.")
                continue

            for i, chunk in enumerate(chunks):
                # Gemini embedding API has a token limit per request.
                # For very long chunks, this might fail. A more advanced chunking
                # strategy would be needed for production.
                embedding = get_embedding(chunk)
                if embedding is None:
                    print(f"Skipping chunk {i+1} from {file_path} due to embedding generation failure.")
                    continue

                document = {
                    "source_file": os.path.relpath(file_path, docs_path),
                    "content": chunk,
                    "embedding": embedding,
                    "chunk_index": i # Add chunk index for better tracking
                }
                documents_to_insert.append(document)
                print(f"Prepared chunk {i+1} from {file_path}")
                time.sleep(0.6) # Add a delay to respect API rate limits

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    if documents_to_insert:
        try:
            # Clear existing documents before inserting new ones to avoid duplicates
            collection.delete_many({})
            collection.insert_many(documents_to_insert)
            print(f"Successfully inserted {len(documents_to_insert)} documents into 'product_knowledge_base'.")
        except Exception as e:
            print(f"Error inserting documents into MongoDB: {e}")
    else:
        print("No documents to insert.")

    client.close()
    print("Knowledge base seeding process completed.")

if __name__ == "__main__":
    seed_knowledge_base()
