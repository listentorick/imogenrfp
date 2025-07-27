import React, { useState, useCallback } from 'react';
import { MagnifyingGlassIcon, XMarkIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import { searchProjectDocuments } from '../utils/api';

const AskImogenTab = ({ projectId }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [showDebugChunks, setShowDebugChunks] = useState(false);
  const [debugChunks, setDebugChunks] = useState(null);
  const [isClearing, setIsClearing] = useState(false);
  const [isReprocessing, setIsReprocessing] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    setSearchError(null);
    try {
      const results = await searchProjectDocuments(projectId, searchQuery);
      setSearchResults(results);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Search failed:', error);
      const errorMessage = error.response?.data?.detail || 'Search failed. Please try again.';
      setSearchError(errorMessage);
      setShowSearchResults(true);
    } finally {
      setIsSearching(false);
    }
  }, [projectId, searchQuery]);

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
    setShowSearchResults(false);
    setSearchError(null);
  };

  const handleShowChunks = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('Fetching chunks for project:', projectId);
      console.log('Using token:', token ? 'Token present' : 'No token');
      
      const response = await fetch(`http://localhost:8000/projects/${projectId}/documents/debug`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        alert(`Error: ${response.status} - ${errorText}`);
        return;
      }
      
      const data = await response.json();
      console.log('Debug chunks data:', data);
      setDebugChunks(data);
      setShowDebugChunks(true);
    } catch (error) {
      console.error('Error fetching debug chunks:', error);
      alert(`Error fetching chunks: ${error.message}`);
    }
  };

  const handleClearChunks = async () => {
    if (!window.confirm('Are you sure you want to clear all chunks? This will remove all vector embeddings for this project.')) {
      return;
    }
    
    setIsClearing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/projects/${projectId}/documents/clear-chunks`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        alert(`Error: ${response.status} - ${errorText}`);
        return;
      }
      
      const data = await response.json();
      alert(data.message);
      setShowDebugChunks(false);
      setDebugChunks(null);
    } catch (error) {
      console.error('Error clearing chunks:', error);
      alert(`Error clearing chunks: ${error.message}`);
    } finally {
      setIsClearing(false);
    }
  };

  const handleReprocessDocuments = async () => {
    if (!window.confirm('Are you sure you want to reprocess all documents with LangChain chunking? This may take a few minutes.')) {
      return;
    }
    
    setIsReprocessing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/projects/${projectId}/documents/reprocess`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        alert(`Error: ${response.status} - ${errorText}`);
        return;
      }
      
      const data = await response.json();
      alert(data.message);
    } catch (error) {
      console.error('Error reprocessing documents:', error);
      alert(`Error reprocessing documents: ${error.message}`);
    } finally {
      setIsReprocessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Ask Imogen Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="bg-blue-600 rounded-full p-2">
            <ChatBubbleLeftRightIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Ask Imogen</h2>
            <p className="text-gray-600">Search through your project documents using AI-powered vector search</p>
          </div>
        </div>
        
        {/* Search Interface */}
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Ask Imogen about your documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={handleSearchKeyPress}
                  className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                />
                <MagnifyingGlassIcon className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
                {searchQuery && (
                  <button
                    onClick={clearSearch}
                    className="absolute right-3 top-3.5 text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                )}
              </div>
            </div>
            <button
              onClick={handleSearch}
              disabled={!searchQuery.trim() || isSearching}
              className="bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {isSearching ? 'Searching...' : 'Ask Imogen'}
            </button>
            <button
              onClick={handleShowChunks}
              className="bg-gray-600 text-white py-3 px-4 rounded-lg hover:bg-gray-700 font-medium"
            >
              Show Chunks
            </button>
          </div>
        </div>
        
        {/* Admin Controls */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h4 className="text-sm font-medium text-yellow-800">LangChain Migration Controls</h4>
              <p className="text-xs text-yellow-700">Manage the transition to LangChain chunking</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleClearChunks}
              disabled={isClearing}
              className="bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700 disabled:bg-gray-400 text-sm"
            >
              {isClearing ? 'Clearing...' : 'Clear All Chunks'}
            </button>
            <button
              onClick={handleReprocessDocuments}
              disabled={isReprocessing}
              className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400 text-sm"
            >
              {isReprocessing ? 'Reprocessing...' : 'Reprocess with LangChain'}
            </button>
          </div>
          <p className="text-xs text-yellow-600 mt-2">
            Use "Clear All Chunks" to remove old chunks, then "Reprocess with LangChain" to create new ones.
          </p>
        </div>
        
        {/* Search Suggestions */}
        {!showSearchResults && (
          <div className="mt-4">
            <p className="text-sm text-gray-600 mb-3">Try asking questions like:</p>
            <div className="flex flex-wrap gap-2">
              {[
                "What are the key requirements?",
                "Show me pricing information",
                "Find technical specifications",
                "What are the deadlines?",
                "Search for contact details"
              ].map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => setSearchQuery(suggestion)}
                  className="text-sm bg-white border border-gray-200 rounded-full px-3 py-1 hover:bg-gray-50 text-gray-700"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Search Results */}
      {showSearchResults && (
        <div className="bg-white shadow rounded-lg">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="bg-green-100 rounded-full p-2">
                  <ChatBubbleLeftRightIcon className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    Imogen's Response for "{searchQuery}"
                  </h3>
                  {searchResults && (
                    <p className="text-sm text-gray-500">
                      Found {searchResults.total_results} relevant section{searchResults.total_results !== 1 ? 's' : ''} in your documents
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={clearSearch}
                className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1"
              >
                <XMarkIcon className="h-4 w-4" />
                <span>Clear</span>
              </button>
            </div>
            
            {searchError ? (
              <div className="text-center py-8">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="text-red-800 font-medium mb-2">Search Error</div>
                  <div className="text-red-600 text-sm">{searchError}</div>
                </div>
              </div>
            ) : searchResults?.results.length === 0 ? (
              <div className="text-center py-8">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="text-yellow-800 font-medium mb-2">No Results Found</div>
                  <div className="text-yellow-700 text-sm">
                    Imogen couldn't find any documents matching your search query. Try rephrasing your question or using different keywords.
                  </div>
                </div>
              </div>
            ) : searchResults ? (
              <div className="space-y-4">
                {searchResults.results.map((result, index) => (
                  <div 
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-gray-900">{result.filename}</h4>
                        <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
                          Section {result.chunk_index + 1} of {result.total_chunks}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="text-xs text-gray-500">
                          Relevance: {Math.max(0, ((1 - result.distance) * 100)).toFixed(0)}%
                        </div>
                        <div className={`w-2 h-2 rounded-full ${
                          result.distance < 0.3 ? 'bg-green-500' : 
                          result.distance < 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}></div>
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-700 leading-relaxed">
                        {result.content.length > 400 
                          ? `${result.content.substring(0, 400)}...` 
                          : result.content
                        }
                      </p>
                    </div>
                    
                    {result.content.length > 400 && (
                      <button className="mt-2 text-sm text-blue-600 hover:text-blue-800">
                        Show full content
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="animate-pulse">
                  <div className="bg-gray-200 rounded-lg h-4 w-3/4 mx-auto mb-2"></div>
                  <div className="bg-gray-200 rounded-lg h-4 w-1/2 mx-auto"></div>
                </div>
                <p className="text-gray-500 mt-2">Imogen is thinking...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Debug Chunks Display */}
      {showDebugChunks && debugChunks && (
        <div className="bg-white shadow rounded-lg">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  Document Chunks Debug View
                </h3>
                <p className="text-sm text-gray-500">
                  Total documents: {debugChunks.total_documents} | Project: {debugChunks.project_id}
                </p>
              </div>
              <button
                onClick={() => setShowDebugChunks(false)}
                className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1"
              >
                <span>Hide</span>
              </button>
            </div>
            
            <div className="space-y-4">
              {debugChunks.documents?.map((doc, index) => (
                <div 
                  key={doc.id || index}
                  className="border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">
                        Chunk {(doc.metadata?.chunk_index || 0) + 1}
                      </h4>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {doc.metadata?.filename || 'Unknown file'}
                      </span>
                      <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                        {doc.content?.length || 0} chars
                      </span>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                      {doc.content}
                    </pre>
                  </div>
                  
                  {doc.metadata && (
                    <div className="mt-3 text-xs text-gray-500">
                      <strong>Metadata:</strong> {JSON.stringify(doc.metadata, null, 2)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AskImogenTab;