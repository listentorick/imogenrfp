#!/usr/bin/env python3
"""
Try ChromaDB with different client configurations
"""
import os
import sys
sys.path.append("/app")

try:
    import chromadb
    from chromadb.config import Settings
    print("📦 ChromaDB module imported successfully")
    
    chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
    chroma_port = os.getenv('CHROMA_PORT', '8000')
    
    print(f"🔌 Connecting to ChromaDB at {chroma_host}:{chroma_port}")
    
    # Try different client configurations
    configs_to_try = [
        ("Standard HttpClient", lambda: chromadb.HttpClient(host=chroma_host, port=int(chroma_port))),
        ("HttpClient with legacy settings", lambda: chromadb.HttpClient(
            host=chroma_host, 
            port=int(chroma_port),
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )),
        ("Client with no tenant", lambda: chromadb.Client()),
    ]
    
    for config_name, client_factory in configs_to_try:
        print(f"\n🧪 Trying: {config_name}")
        try:
            if config_name == "Client with no tenant":
                # Skip this for now as it won't work in Docker
                print("   ⏭️  Skipping local client in Docker environment")
                continue
                
            client = client_factory()
            print("   ✅ Client created successfully")
            
            # Try to list collections
            try:
                collections = client.list_collections()
                print(f"   📚 Found {len(collections)} collections")
                
                for collection in collections:
                    print(f"      - {collection.name}")
                    
                    # Check if it's our project collection
                    if collection.name == "f3a428bb-6659-4a60-81a4-23d2433890a6":
                        count = collection.count()
                        print(f"        🎯 Spectra project collection with {count} items!")
                        
                        if count > 0:
                            # Get a sample
                            results = collection.get(limit=1, include=['documents', 'metadatas'])
                            if results.get('documents'):
                                doc = results['documents'][0]
                                meta = results['metadatas'][0]
                                print(f"        📄 Sample: {meta.get('filename', 'Unknown')} - {doc[:50]}...")
                                
                # If we got this far, this config works!
                print(f"   🎉 SUCCESS with {config_name}!")
                break
                
            except Exception as list_error:
                print(f"   ❌ Failed to list collections: {list_error}")
                
        except Exception as client_error:
            print(f"   ❌ Failed to create client: {client_error}")
    
    else:
        print("\n💀 No configuration worked")
        
        # Last resort: try to test the raw HTTP API
        print("\n🔧 Testing raw HTTP API...")
        import requests
        
        try:
            # Test heartbeat
            response = requests.get(f"http://{chroma_host}:{chroma_port}/api/v1/heartbeat", timeout=5)
            print(f"   Heartbeat v1: {response.status_code}")
        except:
            pass
            
        try:
            response = requests.get(f"http://{chroma_host}:{chroma_port}/api/v1/version", timeout=5)
            print(f"   Version v1: {response.status_code} - {response.text[:100]}")
        except:
            pass
    
except Exception as e:
    print(f"💥 Failed to import or connect: {e}")

print("\n🏁 Check complete")