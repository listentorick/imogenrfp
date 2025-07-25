import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { api } from '../utils/api';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';

const ProjectDetail = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [showUploadModal, setShowUploadModal] = useState(false);

  console.log('ProjectDetail loaded with projectId:', projectId);

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
    <div>
      <div className="mb-6">
        <button
          onClick={() => navigate('/projects')}
          className="flex items-center text-blue-600 hover:text-blue-800 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Back to Projects
        </button>
        
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h1>
          {project.description && (
            <p className="text-gray-600 mb-4">{project.description}</p>
          )}
          <div className="text-sm text-gray-500">
            Created {new Date(project.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <DocumentList 
            projectId={projectId}
            onUploadClick={() => setShowUploadModal(true)}
          />
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Project Actions</h3>
          <div className="space-y-3">
            <button
              onClick={() => navigate(`/standard-answers?project_id=${projectId}`)}
              className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-md transition-colors"
            >
              <div className="font-medium text-gray-900">Standard Answers</div>
              <div className="text-sm text-gray-600">Manage knowledge base for this project</div>
            </button>
            
            <button
              onClick={() => navigate(`/rfp-requests?project_id=${projectId}`)}
              className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-md transition-colors"
            >
              <div className="font-medium text-gray-900">RFP Requests</div>
              <div className="text-sm text-gray-600">View and manage RFP requests</div>
            </button>
          </div>
        </div>
      </div>

      {showUploadModal && (
        <DocumentUpload
          projectId={projectId}
          onClose={() => setShowUploadModal(false)}
        />
      )}
    </div>
  );
};

export default ProjectDetail;