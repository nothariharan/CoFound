import os
from pymongo import MongoClient
import glob
from dotenv import load_dotenv

# Placeholder for an embedding function
def get_embedding(text: str):
    """
    Generates a dummy embedding for the given text.
    In a real application, this would call an LLM like Gemini 2.5 Pro.
    """
    # Return a dummy embedding of 1536 dimensions (matching the index definition)
    return [float(ord(c) % 100) / 100.0 for c in text[:1536].ljust(1536)]

def seed_knowledge_base():
    load_dotenv() # Load environment variables from .env file

    # Retrieve MongoDB URI from environment variables
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MONGODB_URI environment variable not set.")
        return

    client = MongoClient(mongodb_uri)
    db = client.cofounder # Assuming the database name is 'cofounder'
    collection = db.product_knowledge_base

    print("Seeding product_knowledge_base collection with framework documents...")

    docs_path = os.path.join(os.path.dirname(__file__), "..", "docs")
    markdown_files = glob.glob(os.path.join(docs_path, "**", "*.md"), recursive=True)

    if not markdown_files:
        print(f"No markdown files found in {docs_path}. Exiting.")
        return

    documents_to_insert = []
    for file_path in markdown_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # For simplicity, treating the whole file as one chunk.
            # In a real scenario, content would be chunked.
            embedding = get_embedding(content)

            document = {
                "source_file": os.path.relpath(file_path, docs_path),
                "content": content,
                "embedding": embedding
            }
            documents_to_insert.append(document)
            print(f"Prepared document from {file_path}")

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    if documents_to_insert:
        try:
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
