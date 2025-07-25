import React from 'react';
import { useQuery } from 'react-query';
import { api } from '../utils/api';
import {
  FolderIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  RectangleStackIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const { data: projects } = useQuery('projects', () => api.get('/projects/').then(res => res.data));
  const { data: standardAnswers } = useQuery('standard-answers', () => api.get('/standard-answers/').then(res => res.data));
  const { data: rfpRequests } = useQuery('rfp-requests', () => api.get('/rfp-requests/').then(res => res.data));
  const { data: templates } = useQuery('templates', () => api.get('/templates/').then(res => res.data));

  const stats = [
    {
      name: 'Projects',
      count: projects?.length || 0,
      icon: FolderIcon,
      color: 'bg-blue-500'
    },
    {
      name: 'Standard Answers',
      count: standardAnswers?.length || 0,
      icon: DocumentTextIcon,
      color: 'bg-green-500'
    },
    {
      name: 'RFP Requests',
      count: rfpRequests?.length || 0,
      icon: ClipboardDocumentListIcon,
      color: 'bg-yellow-500'
    },
    {
      name: 'Templates',
      count: templates?.length || 0,
      icon: RectangleStackIcon,
      color: 'bg-purple-500'
    }
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Overview of your RFP management system
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((item) => (
          <div key={item.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`${item.color} rounded-md p-3`}>
                    <item.icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {item.name}
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {item.count}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Projects</h3>
          {projects && projects.length > 0 ? (
            <ul className="space-y-3">
              {projects.slice(0, 5).map((project) => (
                <li key={project.id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{project.name}</p>
                    <p className="text-sm text-gray-500">{project.description}</p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No projects yet. Create your first project to get started.</p>
          )}
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent RFP Requests</h3>
          {rfpRequests && rfpRequests.length > 0 ? (
            <ul className="space-y-3">
              {rfpRequests.slice(0, 5).map((rfp) => (
                <li key={rfp.id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{rfp.title}</p>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        rfp.status === 'completed' ? 'bg-green-100 text-green-800' :
                        rfp.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {rfp.status}
                      </span>
                      {rfp.client_name && (
                        <span className="text-sm text-gray-500">for {rfp.client_name}</span>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(rfp.created_at).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No RFP requests yet. Create your first RFP to get started.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;