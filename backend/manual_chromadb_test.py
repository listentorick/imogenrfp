#!/usr/bin/env python3
"""
Manually test ChromaDB storage and search to debug the issue
"""
import requests
import json

def test_chromadb_manually():
    base_url = "http://chromadb:8000/api/v1"
    project_id = "f3a428bb-6659-4a60-81a4-23d2433890a6"
    
    print("=== Manual ChromaDB Test ===")
    
    # Test 1: Create collection
    print("\n1. Creating collection...")
    create_data = {
        "name": project_id,
        "metadata": {"project_name": "Spectra Project"}
    }
    
    try:
        response = requests.post(f"{base_url}/collections", json=create_data)
        print(f"Create collection response: {response.status_code}")
        if response.status_code not in [200, 409]:  # 409 = already exists
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Create collection failed: {e}")
    
    # Test 2: Add sample document about Heritage
    print("\n2. Adding sample document...")
    sample_chunks = [
        "HeritageAdvisor is a comprehensive software solution for heritage management and preservation.",
        "Our heritage management system provides detailed product overview and features for cultural institutions.",
        "The Heritage voice feature allows for audio documentation and preservation of cultural heritage.",
        "Heritage preservation requires detailed documentation and systematic approach to cultural asset management."
    ]
    
    add_data = {
        "documents": sample_chunks,
        "metadatas": [
            {
                "document_id": "sample-heritage-doc",
                "project_id": project_id,
                "filename": "HeritageAdvisor_Sample.docx",
                "chunk_index": i,
                "total_chunks": len(sample_chunks)
            }
            for i in range(len(sample_chunks))
        ],
        "ids": [f"sample-heritage-doc_chunk_{i}" for i in range(len(sample_chunks))]
    }
    
    try:
        response = requests.post(f"{base_url}/collections/{project_id}/add", json=add_data)
        print(f"Add document response: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
        else:
            print("✅ Sample heritage document added successfully!")
    except Exception as e:
        print(f"Add document failed: {e}")
    
    # Test 3: Search for "heritage"
    print("\n3. Testing search for 'heritage'...")
    search_data = {
        "query_texts": ["heritage"],
        "n_results": 5
    }
    
    try:
        response = requests.post(f"{base_url}/collections/{project_id}/query", json=search_data)
        print(f"Search response: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            documents = results.get('documents', [[]])[0]
            distances = results.get('distances', [[]])[0]
            print(f"✅ Found {len(documents)} results:")
            for i, (doc, distance) in enumerate(zip(documents, distances)):
                print(f"  {i+1}. Distance: {distance:.4f} - {doc[:100]}...")
        else:
            print(f"Search failed: {response.text}")
    except Exception as e:
        print(f"Search failed: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_chromadb_manually()