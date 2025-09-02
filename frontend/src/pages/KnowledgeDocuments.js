import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { api } from '../utils/api';
import { ArrowLeftIcon, PlusIcon } from '@heroicons/react/24/outline';
import DocumentUpload from '../components/DocumentUpload';
import DocumentsTable from '../components/DocumentsTable';

const KnowledgeDocuments = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [showUploadModal, setShowUploadModal] = useState(false);

  const { data: project, isLoading } = useQuery(
    ['project', projectId],
    () => api.get(`/projects/`).then(res => 
      res.data.find(p => p.id === projectId)
    ),
    { enabled: !!projectId }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Project not found</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Knowledge Base
            </h1>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Knowledge documents for semantic search and AI question answering
            </div>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Upload Document
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <DocumentsTable 
        projectId={projectId}
        onUploadClick={() => setShowUploadModal(true)}
        showHeader={false}
      />

      {/* Upload Modal */}
      {showUploadModal && (
        <DocumentUpload
          projectId={projectId}
          onClose={() => setShowUploadModal(false)}
        />
      )}
    </div>
  );
};

export default KnowledgeDocuments;