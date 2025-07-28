#!/usr/bin/env python3
import requests
import json
import sys

def test_ollama(prompt, model="qwen3:4b"):
    """Test Ollama with a given prompt"""
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        print(f"🤖 Sending to Ollama: {prompt}")
        print("-" * 50)
        
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        answer = result.get("response", "No response")
        
        # Remove thinking tags for cleaner output
        if "<think>" in answer and "</think>" in answer:
            answer = answer.split("</think>")[-1].strip()
        
        print(f"📝 Response: {answer}")
        print(f"⏱️  Duration: {result.get('total_duration', 0) / 1e9:.2f} seconds")
        return answer
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Enter your prompt: ")
    
    test_ollama(prompt)