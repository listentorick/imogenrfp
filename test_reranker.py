#!/usr/bin/env python3
"""Test script for reranker service integration"""

import requests
import time
import json

def test_reranker_service():
    """Test the reranker service directly"""
    
    # Wait for service to be ready
    print("Waiting for reranker service...")
    for i in range(30):
        try:
            response = requests.get("http://localhost:8002/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ Reranker service is ready: {response.json()}")
                break
        except:
            pass
        time.sleep(2)
        print(f"  Attempt {i+1}/30...")
    else:
        print("✗ Reranker service failed to start")
        return False
    
    # Test reranking
    test_query = "What is the capital of France?"
    test_passages = [
        "Paris is the capital and most populous city of France.",
        "London is the capital of the United Kingdom.",
        "The Eiffel Tower is located in Paris, France.",
        "Berlin is the capital of Germany.",
        "France is a country in Western Europe."
    ]
    
    print(f"\nTesting reranking with query: '{test_query}'")
    print(f"Original passages: {len(test_passages)}")
    
    try:
        response = requests.post(
            "http://localhost:8002/rerank",
            json={
                "query": test_query,
                "passages": test_passages,
                "top_k": 3
            },
            timeout=60
        )
        
        if response.status_code == 200:
            results = response.json()
            print("✓ Reranking successful!")
            print("\nTop ranked passages:")
            for i, result in enumerate(results['results']):
                print(f"  {i+1}. Score: {result['score']:.4f} | Index: {result['index']} | Text: {result['text'][:80]}...")
            return True
        else:
            print(f"✗ Reranking failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Reranking error: {e}")
        return False

if __name__ == "__main__":
    test_reranker_service()