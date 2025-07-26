import React, { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { api, searchProjectDocuments } from '../utils/api';
import { ArrowLeftIcon, MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import DocumentUpload from '../components/DocumentUpload';
import DocumentsTable from '../components/DocumentsTable';
import DealsTable from '../components/DealsTable';
import DealForm from '../components/DealForm';

const ProjectDetail = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [showCreateDeal, setShowCreateDeal] = useState(false);
  const [activeTab, setActiveTab] = useState('deals');

  console.log('ProjectDetail loaded with projectId:', projectId);

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

  const { data: project, isLoading } = useQuery(
    ['project', projectId],
    () => api.get(`/projects/`).then(res => 
      res.data.find(p => p.id === projectId)
    ),
    {
      enabled: !!projectId
    }
  );

  if (isLoading) {
    return <div className="flex justify-center py-8">Loading project...</div>;
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Project not found</h3>
        <button
          onClick={() => navigate('/projects')}
          className="text-blue-600 hover:text-blue-800"
        >
          Back to Projects
        </button>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <button
          onClick={() => navigate('/projects')}
          className="flex items-center text-blue-600 hover:text-blue-800 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Back to Projects
        </button>
        
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h1>
              {project.description && (
                <p className="text-gray-600 mb-2">{project.description}</p>
              )}
              <div className="text-sm text-gray-500">
                Created {new Date(project.created_at).toLocaleDateString()}
              </div>
            </div>
            
            {/* Search Bar - Only show on documents tab */}
            {activeTab === 'documents' && (
              <div className="flex-shrink-0 ml-6 w-80">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search documents..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={handleSearchKeyPress}
                    className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                  {searchQuery && (
                    <button
                      onClick={clearSearch}
                      className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  )}
                </div>
                <button
                  onClick={handleSearch}
                  disabled={!searchQuery.trim() || isSearching}
                  className="mt-2 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                >
                  {isSearching ? 'Searching...' : 'Search'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Search Results */}
      {showSearchResults && (
        <div className="mb-6">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">
                Search Results for "{searchQuery}"
              </h2>
              {searchResults && (
                <div className="text-sm text-gray-500">
                  {searchResults.total_results} result{searchResults.total_results !== 1 ? 's' : ''}
                </div>
              )}
            </div>
            
            {searchError ? (
              <div className="text-center py-8">
                <div className="text-red-600 mb-2">Search Error</div>
                <div className="text-gray-600 text-sm">{searchError}</div>
              </div>
            ) : searchResults?.results.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No documents found matching your search query.
              </div>
            ) : searchResults ? (
              <div className="space-y-4">
                {searchResults.results.map((result, index) => (
                  <div 
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="font-medium text-gray-900">{result.filename}</h3>
                          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                            Chunk {result.chunk_index + 1} of {result.total_chunks}
                          </span>
                        </div>
                        <p className="text-gray-600 text-sm leading-relaxed">
                          {result.content.length > 300 
                            ? `${result.content.substring(0, 300)}...` 
                            : result.content
                          }
                        </p>
                      </div>
                      <div className="flex-shrink-0 ml-4">
                        <div className="text-xs text-gray-500">
                          Relevance: {(1 - result.distance).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                Loading search results...
              </div>
            )}
            
            <div className="mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={clearSearch}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Clear search results
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('deals')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'deals'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Deals
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Documents
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="mb-6">
        {activeTab === 'deals' && (
          <DealsTable 
            projectId={projectId}
            onCreateDeal={() => setShowCreateDeal(true)}
          />
        )}
        
        {activeTab === 'documents' && (
          <DocumentsTable 
            projectId={projectId}
            onUploadClick={() => setShowUploadModal(true)}
          />
        )}
      </div>

      {showUploadModal && (
        <DocumentUpload
          projectId={projectId}
          onClose={() => setShowUploadModal(false)}
        />
      )}

      {showCreateDeal && (
        <DealForm
          projectId={projectId}
          onClose={() => setShowCreateDeal(false)}
          onSuccess={() => window.location.reload()} // Simple refresh for now
        />
      )}
    </div>
  );
};

export default ProjectDetail;