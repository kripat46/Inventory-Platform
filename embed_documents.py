import os
from openai import OpenAI
from pinecone import Pinecone

def run_pinecone_rag_pipeline():
    print("Initializing Pinecone Serverless Vector Ingestion Engine...")
    
    # 1. API Credentials Configuration
    # Replace these strings with your real secret keys:
    OPENAI_API_KEY = "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"
    PINECONE_API_KEY = "pcsk_6pBXB2_7EnyeZVgWXoJFaqPLL1U3pGcGNWi8scUBo83MoQc1NaFkWPxQ1ULMdNJ6QmuNPE"
    INDEX_NAME = "inventory-rag-index"
    
    # 2. Instantiate External Cloud Clients
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Establish connection to your active vector database index
    pinecone_index = pc.Index(INDEX_NAME)
    
    # 3. Read Your Generated Unstructured Logistics Files
    unstructured_dir = os.path.join("data", "unstructured")
    if not os.path.exists(unstructured_dir):
        print("[ERROR] Unstructured text data folder empty. Run your generator script first.")
        return
        
    vectors_to_upsert = []
    file_count = 0
    
    # 4. Loop Through Text Documents and Vectorize
    for filename in os.listdir(unstructured_dir):
        if filename.endswith(".txt"):
            file_count += 1
            file_path = os.path.join(unstructured_dir, filename)
            
            with open(file_path, "r", encoding="utf-8") as f:
                document_content = f.read()
                
            print(f"[{file_count}] Vectorizing logistics record via OpenAI: {filename}...")
            
            # Generate multi-dimensional coordinates using OpenAI's lowest-cost embedding tool
            response = openai_client.embeddings.create(
                input=document_content,
                model="text-embedding-3-small"
            )
            embedding_coordinates = response.data[0].embedding
            
            # Formulate metadata tags so the GenAI Agent can read/filter text context later
            metadata = {
                "filename": filename,
                "text": document_content,
                "data_type": "logistics_incident_report"
            }
            
            # Pack payload strictly following Pinecone specifications
            vectors_to_upsert.append({
                "id": f"doc_id_{file_count}", 
                "values": embedding_coordinates, 
                "metadata": metadata
            })
            
    # 5. Batch Stream Data Directly to the Cloud
    print(f"\nStreaming {len(vectors_to_upsert)} vector nodes up to Pinecone Serverless Cloud...")
    pinecone_index.upsert(vectors=vectors_to_upsert)
    
    print("\n[SUCCESS] Unstructured Cloud RAG Pipeline executed perfectly!")
    print(f"All {file_count} logistics configurations are live inside Pinecone Serverless.")

if __name__ == "__main__":
    run_pinecone_rag_pipeline()
