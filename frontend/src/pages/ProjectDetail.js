import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../utils/api';
import { ArrowLeftIcon, PencilIcon } from '@heroicons/react/24/outline';
import DocumentUpload from '../components/DocumentUpload';
import DocumentsTable from '../components/DocumentsTable';
import DealsTable from '../components/DealsTable';
import DealForm from '../components/DealForm';
import AskImogenTab from '../components/AskImogenTab';

const ProjectDetail = () => {
  const { projectId, tab } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showCreateDeal, setShowCreateDeal] = useState(false);
  const [activeTab, setActiveTab] = useState('deals');
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});

  // Extract tab from URL path params
  useEffect(() => {
    const validTabs = ['deals', 'documents', 'ask-imogen'];
    
    if (tab && validTabs.includes(tab)) {
      setActiveTab(tab);
    } else if (tab && !validTabs.includes(tab)) {
      // Redirect to deals tab if invalid tab is provided
      navigate(`/projects/${projectId}/deals`, { replace: true });
    } else if (!tab) {
      // Default to deals tab if no tab is specified
      setActiveTab('deals');
    }
  }, [tab, projectId, navigate]);

  // Function to handle tab changes and update URL
  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    navigate(`/projects/${projectId}/${newTab}`, { replace: true });
  };

  console.log('ProjectDetail loaded with projectId:', projectId);

  const { data: project, isLoading } = useQuery(
    ['project', projectId],
    () => api.get(`/projects/`).then(res => 
      res.data.find(p => p.id === projectId)
    ),
    {
      enabled: !!projectId,
      onSuccess: (data) => {
        if (data && !isEditing) {
          setEditData({
            name: data.name,
            description: data.description || ''
          });
        }
      }
    }
  );

  const updateProjectMutation = useMutation(
    (data) => api.put(`/projects/${projectId}`, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['project', projectId]);
        setIsEditing(false);
      }
    }
  );

  const deleteProjectMutation = useMutation(
    () => api.delete(`/projects/${projectId}`),
    {
      onSuccess: () => {
        navigate('/projects');
      }
    }
  );

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    if (project) {
      setEditData({
        name: project.name,
        description: project.description || ''
      });
    }
  };

  const handleSaveEdit = () => {
    updateProjectMutation.mutate(editData);
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this project? This will also delete all associated deals and documents.')) {
      deleteProjectMutation.mutate();
    }
  };

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
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              {isEditing ? (
                <input
                  type="text"
                  value={editData.name}
                  onChange={(e) => setEditData(prev => ({ ...prev, name: e.target.value }))}
                  className="text-2xl font-bold text-gray-900 border-b-2 border-blue-500 bg-transparent focus:outline-none mb-2"
                />
              ) : (
                <h1 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h1>
              )}
              
              {isEditing ? (
                <textarea
                  value={editData.description}
                  onChange={(e) => setEditData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  className="w-full text-gray-600 border border-gray-300 rounded-md p-3 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter project description..."
                />
              ) : (
                project.description && (
                  <p className="text-gray-600 mb-2">{project.description}</p>
                )
              )}
              
              <div className="text-sm text-gray-500">
                Created {new Date(project.created_at).toLocaleDateString()}
              </div>
            </div>
            
            <div className="flex space-x-2">
              {isEditing ? (
                <>
                  <button
                    onClick={handleSaveEdit}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    disabled={updateProjectMutation.isLoading}
                  >
                    {updateProjectMutation.isLoading ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleEdit}
                    className="flex items-center px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    <PencilIcon className="h-4 w-4 mr-2" />
                    Edit
                  </button>
                  <button
                    onClick={handleDelete}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                    disabled={deleteProjectMutation.isLoading}
                  >
                    {deleteProjectMutation.isLoading ? 'Deleting...' : 'Delete'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>


      {/* Tabs Navigation */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => handleTabChange('deals')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'deals'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Deals
            </button>
            <button
              onClick={() => handleTabChange('documents')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Documents
            </button>
            <button
              onClick={() => handleTabChange('ask-imogen')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'ask-imogen'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Ask Imogen
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
        
        {activeTab === 'ask-imogen' && (
          <AskImogenTab projectId={projectId} />
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