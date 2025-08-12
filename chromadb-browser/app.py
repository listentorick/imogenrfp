#!/usr/bin/env python3
"""
ChromaDB Browser UI using v2 API
Connects to ChromaDB and provides a web interface to browse collections and documents
"""
import os
import chromadb
from flask import Flask, render_template, jsonify, request
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class ChromaDBBrowser:
    def __init__(self):
        chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
        chroma_port = int(os.getenv('CHROMA_PORT', '8000'))
        
        try:
            # Use the same client configuration as your main application
            self.client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
            logger.info(f"Connected to ChromaDB at {chroma_host}:{chroma_port}")
            
            # Test connection by trying to list collections
            self._test_connection()
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    def _test_connection(self):
        """Test the connection by attempting to list collections"""
        try:
            collections = self.client.list_collections()
            logger.info(f"Successfully connected. Found {len(collections)} collections")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
    
    def list_collections(self):
        """List all collections in ChromaDB"""
        try:
            collections = self.client.list_collections()
            result = []
            for col in collections:
                try:
                    # Get collection count
                    collection = self.client.get_collection(name=col.name)
                    count = collection.count()
                    result.append({
                        "name": col.name,
                        "metadata": col.metadata if hasattr(col, 'metadata') else {},
                        "count": count
                    })
                except Exception as e:
                    logger.warning(f"Could not get details for collection {col.name}: {e}")
                    result.append({
                        "name": col.name,
                        "metadata": {},
                        "count": 0
                    })
            return result
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def get_collection_info(self, collection_name):
        """Get detailed information about a collection"""
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()
            metadata = collection.metadata if hasattr(collection, 'metadata') else {}
            return {
                "name": collection_name,
                "count": count,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            return None
    
    def get_collection_documents(self, collection_name, limit=50):
        """Get documents from a collection"""
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Get documents with metadata and IDs (limit the number for performance)
            results = collection.get(
                include=['documents', 'metadatas'],
                limit=limit if limit <= 100 else 100  # Cap at 100 for performance
            )
            
            documents = []
            ids = results.get('ids', [])
            docs = results.get('documents', [])
            metas = results.get('metadatas', [])
            
            for i in range(len(ids)):
                doc = {
                    'id': ids[i],
                    'content': docs[i] if i < len(docs) else '',
                    'metadata': metas[i] if i < len(metas) else {},
                    'content_preview': (docs[i][:200] + '...' if i < len(docs) and len(docs[i]) > 200 else docs[i]) if i < len(docs) else ''
                }
                documents.append(doc)
            
            total_count = collection.count()
            return {
                'documents': documents,
                'total_count': total_count,
                'displayed_count': len(documents)
            }
        except Exception as e:
            logger.error(f"Error getting documents from {collection_name}: {e}")
            return {'documents': [], 'total_count': 0, 'displayed_count': 0}
    
    def search_collection(self, collection_name, query_text, n_results=10):
        """Search within a collection"""
        try:
            collection = self.client.get_collection(name=collection_name)
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            search_results = []
            if results.get('documents') and len(results['documents']) > 0 and len(results['documents'][0]) > 0:
                documents = results['documents'][0]
                metadatas = results.get('metadatas', [[]])[0]
                distances = results.get('distances', [[]])[0]
                
                for i in range(len(documents)):
                    distance = distances[i] if i < len(distances) else 1.0
                    similarity_score = max(0, (1 - distance) * 100)
                    
                    result = {
                        'content': documents[i],
                        'content_preview': documents[i][:300] + '...' if len(documents[i]) > 300 else documents[i],
                        'metadata': metadatas[i] if i < len(metadatas) else {},
                        'distance': distance,
                        'similarity_score': round(similarity_score, 1)
                    }
                    search_results.append(result)
            
            return search_results
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {e}")
            return []

# Initialize ChromaDB browser
try:
    browser = ChromaDBBrowser()
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB browser: {e}")
    browser = None

@app.route('/')
def index():
    """Main dashboard showing all collections"""
    if not browser:
        return "ChromaDB connection failed", 500
    
    collections = browser.list_collections()
    return render_template('index.html', collections=collections)

@app.route('/api/collections')
def api_collections():
    """API endpoint to get all collections"""
    if not browser:
        return jsonify({'error': 'ChromaDB connection failed'}), 500
    
    collections = browser.list_collections()
    return jsonify(collections)

@app.route('/collection/<collection_name>')
def collection_detail(collection_name):
    """View detailed information about a specific collection"""
    if not browser:
        return "ChromaDB connection failed", 500
    
    info = browser.get_collection_info(collection_name)
    if not info:
        return "Collection not found", 404
    
    # Get documents with limit
    limit = int(request.args.get('limit', 50))
    documents_data = browser.get_collection_documents(collection_name, limit=limit)
    
    return render_template('collection.html', 
                         collection=info, 
                         documents=documents_data['documents'],
                         total_count=documents_data['total_count'],
                         displayed_count=documents_data['displayed_count'],
                         limit=limit)

@app.route('/api/collection/<collection_name>/documents')
def api_collection_documents(collection_name):
    """API endpoint to get documents from a collection"""
    if not browser:
        return jsonify({'error': 'ChromaDB connection failed'}), 500
    
    limit = int(request.args.get('limit', 50))
    result = browser.get_collection_documents(collection_name, limit=limit)
    return jsonify(result)

@app.route('/api/collection/<collection_name>/search')
def api_search_collection(collection_name):
    """API endpoint to search within a collection"""
    if not browser:
        return jsonify({'error': 'ChromaDB connection failed'}), 500
    
    query = request.args.get('q', '')
    n_results = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    results = browser.search_collection(collection_name, query, n_results)
    return jsonify({'query': query, 'results': results})

@app.route('/collection/<collection_name>/search')
def collection_search(collection_name):
    """Search interface for a collection"""
    if not browser:
        return "ChromaDB connection failed", 500
    
    query = request.args.get('q', '')
    results = []
    
    if query:
        results = browser.search_collection(collection_name, query)
    
    info = browser.get_collection_info(collection_name)
    return render_template('search.html', 
                         collection=info, 
                         query=query, 
                         results=results)

@app.route('/health')
def health():
    """Health check endpoint"""
    if not browser:
        return jsonify({'status': 'error', 'message': 'ChromaDB connection failed'}), 500
    
    try:
        collections = browser.list_collections()
        return jsonify({
            'status': 'ok', 
            'chromadb_connected': True,
            'collections_count': len(collections)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'chromadb_connected': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)