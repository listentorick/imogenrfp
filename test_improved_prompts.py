#!/usr/bin/env python3
"""
Test the improved question extraction prompts
"""
import requests
import json

def test_text_extraction():
    """Test the improved text extraction prompt"""
    
    # Sample RFP text with various types of requirements
    sample_text = """
    Company Requirements:
    
    1. What is your company's experience with similar projects?
    2. Describe your project management methodology
    3. List all relevant certifications your team holds
    4. Must demonstrate compliance with ISO 27001 standards
    5. Bidders should provide three client references
    6. Technical specifications required:
       - System uptime must be 99.9%
       - Response time should be under 2 seconds
    7. How do you handle data backup and recovery?
    8. Proposals must include detailed project timeline
    """
    
    # Test with Ollama directly
    ollama_url = "http://localhost:11434/api/generate"
    model = "qwen3:4b"
    
    prompt = f"""
You are tasked with extracting questions and requirements from a document. Analyze the following text and identify all items that request information, regardless of how they are phrased.

Look for:
- Direct questions (e.g., "What is your experience?", "How do you handle security?")
- Requirements (e.g., "Describe your methodology", "Provide details of your approach")
- Criteria statements (e.g., "Must demonstrate compliance with", "Should include examples of")
- Information requests (e.g., "List your certifications", "Outline your process")
- Specification needs (e.g., "Technical specifications required", "Documentation must include")
- Evaluation criteria (e.g., "Bidders must provide evidence of", "Proposals should address")

Convert each item into a clear question format while preserving the original intent and context.

Return your response as a JSON array where each item is an object with:
- "question": the item converted to a clear question format (if not already a question)
- "original_text": the exact original text from the document  
- "confidence": a confidence score from 0.0 to 1.0 indicating how certain you are this requires a response
- "order": the sequential order this item appears in the document (starting from 1)
- "type": the type of request ("question", "requirement", "criteria", "specification", "other")

Document text:
{sample_text}

Response format:
[
    {{"question": "What is your company's experience with similar projects?", "original_text": "What is your company's experience with similar projects?", "confidence": 0.95, "order": 1, "type": "question"}},
    {{"question": "How do you ensure data security and compliance?", "original_text": "Must demonstrate compliance with data protection regulations", "confidence": 0.90, "order": 2, "type": "requirement"}},
    {{"question": "What certifications do you hold?", "original_text": "List relevant industry certifications", "confidence": 0.85, "order": 3, "type": "specification"}}
]
"""
    
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }
    
    try:
        print("Testing improved text extraction prompt...")
        response = requests.post(ollama_url, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("response", "").strip()
        
        print(f"Raw response length: {len(response_text)}")
        print(f"Raw response: {response_text[:500]}...")
        
        # Try to extract JSON
        start_idx = response_text.find('[')
        if start_idx != -1:
            bracket_count = 0
            end_idx = -1
            
            for i in range(start_idx, len(response_text)):
                if response_text[i] == '[':
                    bracket_count += 1
                elif response_text[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i
                        break
            
            if end_idx != -1:
                json_text = response_text[start_idx:end_idx + 1]
                try:
                    questions = json.loads(json_text)
                    print(f"\n✅ Successfully extracted {len(questions)} items:")
                    for i, q in enumerate(questions):
                        print(f"{i+1}. {q.get('type', 'unknown').upper()}: {q.get('question', 'N/A')}")
                        print(f"   Original: {q.get('original_text', 'N/A')}")
                        print(f"   Confidence: {q.get('confidence', 0):.2f}")
                        print()
                    return True
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    return False
        
        print("❌ No valid JSON found in response")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_text_extraction()