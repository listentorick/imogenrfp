#!/usr/bin/env python3
"""
Simple ChromaDB check using the same method as document_processor
"""
import os
import sys
sys.path.append("/app")

try:
    import chromadb
    print("📦 ChromaDB module imported successfully")
    
    chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
    chroma_port = os.getenv('CHROMA_PORT', '8000')
    
    print(f"🔌 Connecting to ChromaDB at {chroma_host}:{chroma_port}")
    
    # Use the same connection method as document_processor
    client = chromadb.HttpClient(
        host=chroma_host,
        port=int(chroma_port)
    )
    
    print("✅ ChromaDB client created")
    
    # Try to list collections (this should work without tenant issues)
    try:
        collections = client.list_collections()
        print(f"📚 Found {len(collections)} collections:")
        
        for collection in collections:
            print(f"   - {collection.name}")
            
            # Try to get collection info
            try:
                count = collection.count()
                print(f"     📊 Contains {count} items")
                
                # If this is our project collection, get some details
                if collection.name == "f3a428bb-6659-4a60-81a4-23d2433890a6":
                    print(f"     🎯 This is the Spectra project collection!")
                    if count > 0:
                        # Get first few items
                        results = collection.get(limit=3, include=['documents', 'metadatas'])
                        docs = results.get('documents', [])
                        metas = results.get('metadatas', [])
                        
                        print(f"     📄 Sample content:")
                        for i, (doc, meta) in enumerate(zip(docs, metas)):
                            print(f"       {i+1}. Document ID: {meta.get('document_id', 'Unknown')}")
                            print(f"          File: {meta.get('filename', 'Unknown')}")
                            print(f"          Preview: {doc[:100]}...")
                    
            except Exception as e:
                print(f"     ❌ Error getting collection details: {e}")
                
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
        
        # Try alternative approach - attempt to get a known collection
        try:
            project_collection = client.get_collection("f3a428bb-6659-4a60-81a4-23d2433890a6")
            print(f"✅ Found project collection directly: {project_collection.name}")
            count = project_collection.count()
            print(f"📊 Collection has {count} items")
            
        except Exception as e2:
            print(f"❌ Could not get project collection directly: {e2}")
            
            # Try to get any collection
            try:
                # Check if documents collection exists (from old code)
                docs_collection = client.get_collection("documents")
                print(f"✅ Found documents collection: {docs_collection.name}")
                count = docs_collection.count()
                print(f"📊 Documents collection has {count} items")
            except Exception as e3:
                print(f"❌ No collections found: {e3}")
    
except Exception as e:
    print(f"💥 Failed to connect to ChromaDB: {e}")

print("\n🏁 ChromaDB check complete")