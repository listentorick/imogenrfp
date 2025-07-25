#!/usr/bin/env python3
"""
Check ChromaDB content and collections
"""
import requests
import json
import os
import chromadb

def check_chromadb():
    # ChromaDB connection details (use container name when running in Docker)
    chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
    chroma_port = os.getenv('CHROMA_PORT', '8000')
    
    print("🔍 Checking ChromaDB content...")
    print(f"📡 Connecting to: {chroma_host}:{chroma_port}")
    print("=" * 50)
    
    try:
        # Use ChromaDB Python client
        client = chromadb.HttpClient(host=chroma_host, port=int(chroma_port))
        
        print("✅ ChromaDB client connected successfully")
        
        # Try to get or create the default tenant
        try:
            client.get_or_create_tenant("default_tenant")
            print("✅ Default tenant available")
        except Exception as tenant_error:
            print(f"⚠️  Tenant issue (continuing anyway): {tenant_error}")
        
        # List all collections
        collections = client.list_collections()
        print(f"📚 Found {len(collections)} collections:")
        
        for collection in collections:
            print(f"   - {collection.name} (metadata: {collection.metadata})")
        
        # Check the specific project collection
        project_id = "f3a428bb-6659-4a60-81a4-23d2433890a6"  # Your spectra project ID
        
        print(f"\n🔍 Examining project collection: {project_id}")
        
        try:
            collection = client.get_collection(name=str(project_id))
            print(f"✅ Collection exists: {collection.name}")
            print(f"📋 Metadata: {json.dumps(collection.metadata, indent=2)}")
            
            # Count documents in collection
            count = collection.count()
            print(f"📊 Collection contains {count} items")
            
            if count > 0:
                # Get sample documents
                results = collection.get(limit=10, include=['documents', 'metadatas'])
                
                documents = results.get('documents', [])
                metadatas = results.get('metadatas', [])
                ids = results.get('ids', [])
                
                print(f"\n📄 Sample document chunks ({min(len(documents), 5)} of {len(documents)}):")
                
                for i, (doc_id, content, metadata) in enumerate(zip(ids[:5], documents[:5], metadatas[:5])):
                    print(f"\n--- Chunk {i+1} ---")
                    print(f"ID: {doc_id}")
                    print(f"Document ID: {metadata.get('document_id', 'Unknown')}")
                    print(f"Filename: {metadata.get('filename', 'Unknown')}")
                    print(f"Chunk Index: {metadata.get('chunk_index', 'Unknown')} / {metadata.get('total_chunks', 'Unknown')}")
                    print(f"Content Preview (first 200 chars): {content[:200]}...")
                
                # Test semantic search
                print(f"\n🔍 Testing semantic search...")
                try:
                    search_results = collection.query(
                        query_texts=["document processing"],
                        n_results=3
                    )
                    
                    search_docs = search_results.get('documents', [[]])[0]
                    search_distances = search_results.get('distances', [[]])[0]
                    
                    print(f"🎯 Search returned {len(search_docs)} results:")
                    for j, (result, distance) in enumerate(zip(search_docs, search_distances)):
                        print(f"   {j+1}. Distance: {distance:.4f} - {result[:100]}...")
                        
                except Exception as search_error:
                    print(f"❌ Search failed: {search_error}")
            else:
                print("📭 Collection is empty")
                
        except Exception as collection_error:
            print(f"❌ Collection {project_id} not found or error: {collection_error}")
            
    except Exception as e:
        print(f"💥 Error connecting to ChromaDB: {e}")
    
    print("\n" + "=" * 50)
    print("✅ ChromaDB check complete")

if __name__ == "__main__":
    check_chromadb()