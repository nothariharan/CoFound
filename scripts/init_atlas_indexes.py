import os
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from dotenv import load_dotenv
from pymongo.operations import SearchIndexModel # import searchindexmodel

def create_atlas_indexes():
    load_dotenv() # load environment variables from .env file

    # retrieve mongodb uri from environment variables
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MONGODB_URI environment variable not set.")
        return

    client = MongoClient(mongodb_uri)
    db = client.cofounder # assuming the database name is 'cofounder'

    print("Creating Atlas Search and Vector Search indexes...")

    # ensure collections exist before creating search indexes
    # -------------------------------------------------------
    collections_to_ensure = ["startup_graphs", "product_knowledge_base"]
    for col_name in collections_to_ensure:
        try:
            # insert a dummy document to ensure collection exists
            db[col_name].insert_one({"_id": "dummy_doc_for_index_creation", "temp": True})
            # delete the dummy document
            db[col_name].delete_one({"_id": "dummy_doc_for_index_creation"})
            print(f"Ensured collection '{col_name}' exists.")
        except Exception as e:
            print(f"Could not ensure collection '{col_name}' exists: {e}")
    # -------------------------------------------------------

    # 1. startup_graphs: text index on workspace_name
    try:
        text_search_index_model = SearchIndexModel(
            definition={
                "mappings": {
                    "dynamic": True,
                    "fields": {
                        "workspace_name": {
                            "type": "string"
                        }
                    }
                }
            },
            name="startup_graphs_text_index",
            type="search" # specify the type for a text search index
        )
        db.startup_graphs.create_search_index(model=text_search_index_model)
        print("Created text index for 'startup_graphs' collection on 'workspace_name'.")
    except Exception as e:
        print(f"Could not create text index for 'startup_graphs': {e}")

    # 2. product_knowledge_base: vector search index on embedding field
    try:
        vector_search_index_model = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "type": "vector", # corrected type from knnvector to vector
                        "path": "embedding",
                        "numDimensions": 1536, # assuming common embedding size, adjust if needed
                        "similarity": "cosine"
                    }
                ]
            },
            name="product_knowledge_base_vector_index",
            type="vectorSearch" # specify the type for a vector search index
        )
        db.product_knowledge_base.create_search_index(model=vector_search_index_model)
        print("Created vector search index for 'product_knowledge_base' collection on 'embedding'.")
    except Exception as e:
        print(f"Could not create vector search index for 'product_knowledge_base': {e}")

    # 3. task_queue: index on status + priority
    try:
        db.task_queue.create_index([("status", 1), ("priority", -1)])
        print("Created compound index for 'task_queue' collection on 'status' and 'priority'.")
    except Exception as e:
        print(f"Could not create compound index for 'task_queue': {e}")

    client.close()
    print("Index creation process completed.")

if __name__ == "__main__":
    create_atlas_indexes()
