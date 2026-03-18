import chromadb
from chromadb.config import Settings
import os

def test_chroma():
    # 1. Setup ChromaDB with persistent storage
    persist_directory = os.path.join(os.getcwd(), "data", "chroma")
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)
        print(f"Created directory: {persist_directory}")

    client = chromadb.PersistentClient(path=persist_directory)
    print(f"Connected to ChromaDB at {persist_directory}")

    # 2. Create collection
    collection_name = "chronicle_episodes"
    
    # Delete if exists to start fresh for this test
    try:
        client.delete_collection(collection_name)
    except:
        pass
        
    collection = client.create_collection(name=collection_name)
    print(f"Created collection: {collection_name}")

    # 3. Add 5 sample documents
    documents = [
        "The protagonist discovers a hidden portal in the attic.",
        "A quiet rainy day in the city brings unexpected visitors.",
        "Exploring the ruins of an ancient civilization deep in the jungle.",
        "A futuristic skyline filled with flying cars and neon lights.",
        "The mystery of the missing heirloom deepens as a new clue emerges."
    ]
    metadatas = [
        {"genre": "fantasy", "episode": 1},
        {"genre": "drama", "episode": 2},
        {"genre": "adventure", "episode": 3},
        {"genre": "sci-fi", "episode": 4},
        {"genre": "mystery", "episode": 5}
    ]
    ids = ["id1", "id2", "id3", "id4", "id5"]

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print("Added 5 sample documents to the collection.")

    # 4. Query sample text
    query_text = "ancient jungle exploration"
    results = collection.query(
        query_texts=[query_text],
        n_results=2
    )

    print(f"\nQuery: '{query_text}'")
    print("Results:")
    for i in range(len(results['ids'][0])):
        print(f"- ID: {results['ids'][0][i]}")
        print(f"  Document: {results['documents'][0][i]}")
        print(f"  Metadata: {results['metadatas'][0][i]}")
        print(f"  Distance: {results['distances'][0][i]}")

if __name__ == "__main__":
    test_chroma()
