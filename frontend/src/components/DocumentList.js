import React, { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { api } from '../utils/api';
import { DocumentIcon, CloudArrowUpIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';

const DocumentList = ({ projectId, onUploadClick }) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [socket, setSocket] = useState(null);
  
  const { data: documents, isLoading } = useQuery(
    ['project-documents', projectId],
    () => api.get(`/projects/${projectId}/documents`).then(res => res.data),
    {
      enabled: !!projectId
    }
  );

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (user?.tenant_id) {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No authentication token found for WebSocket connection');
        return;
      }
      
      const ws = new WebSocket(`ws://localhost:8000/ws?token=${encodeURIComponent(token)}`);
      
      ws.onopen = () => {
        console.log('DocumentList WebSocket connected with authentication');
        setSocket(ws);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'document_status_update') {
          // Refresh document list when status updates
          queryClient.invalidateQueries(['project-documents', projectId]);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setSocket(null);
      };
      
      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      };
    }
  }, [user?.tenant_id, projectId, queryClient]);

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const badges = {
      uploaded: { 
        text: 'Uploaded', 
        className: 'bg-blue-100 text-blue-800' 
      },
      processing: { 
        text: 'Processing...', 
        className: 'bg-yellow-100 text-yellow-800' 
      },
      processed: { 
        text: 'Processed', 
        className: 'bg-green-100 text-green-800' 
      },
      error: { 
        text: 'Error', 
        className: 'bg-red-100 text-red-800' 
      }
    };
    
    const badge = badges[status] || badges.uploaded;
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.className}`}>
        {badge.text}
      </span>
    );
  };

  const handleDownload = (doc) => {
    const token = localStorage.getItem('token');
    const downloadUrl = `http://localhost:8000/documents/${doc.id}/download`;
    
    console.log('Attempting to download:', downloadUrl);
    console.log('Token exists:', !!token);
    
    // Add authorization header and download the file
    fetch(downloadUrl, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(response => {
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      if (!response.ok) {
        return response.text().then(text => {
          console.error('Error response:', text);
          throw new Error(`Download failed: ${response.status} - ${text}`);
        });
      }
      return response.blob();
    })
    .then(blob => {
      console.log('Blob received, size:', blob.size);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.original_filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    })
    .catch(error => {
      console.error('Download failed:', error);
      alert(`Failed to download file: ${error.message}`);
    });
  };

  if (isLoading) {
    return <div className="text-center py-4">Loading documents...</div>;
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">Documents</h3>
        <button
          onClick={onUploadClick}
          className="bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 flex items-center text-sm"
        >
          <CloudArrowUpIcon className="h-4 w-4 mr-1" />
          Upload
        </button>
      </div>
      
      <div className="divide-y divide-gray-200">
        {documents && documents.length > 0 ? (
          documents.map((document) => (
            <div key={document.id} className="p-4 hover:bg-gray-50">
              <div className="flex items-center">
                <DocumentIcon className="h-5 w-5 text-gray-400 mr-3" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <button
                      onClick={() => handleDownload(document)}
                      className="text-sm font-medium text-blue-600 hover:text-blue-800 truncate text-left"
                      title="Click to download"
                    >
                      {document.original_filename}
                    </button>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(document.status)}
                      <p className="text-xs text-gray-500">
                        {formatFileSize(document.file_size)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                      {document.mime_type}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatDate(document.created_at)}
                    </p>
                  </div>
                  {document.processing_error && (
                    <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                      Error: {document.processing_error}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="p-8 text-center">
            <DocumentIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by uploading your first document
            </p>
            <div className="mt-4">
              <button
                onClick={onUploadClick}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center mx-auto"
              >
                <CloudArrowUpIcon className="h-4 w-4 mr-2" />
                Upload Document
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentList;