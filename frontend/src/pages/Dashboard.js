import React from 'react';
import { useQuery } from 'react-query';
import { api } from '../utils/api';
import {
  FolderIcon,
  RectangleStackIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const { data: projects } = useQuery('projects', () => api.get('/projects/').then(res => res.data));
  const { data: templates } = useQuery('templates', () => api.get('/templates/').then(res => res.data));

  const stats = [
    {
      name: 'Projects',
      count: projects?.length || 0,
      icon: FolderIcon,
      color: 'bg-blue-500'
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Overview of your RFP management system
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((item) => (
          <div key={item.name} className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`${item.color} rounded-md p-3`}>
                    <item.icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                      {item.name}
                    </dt>
                    <dd className="text-lg font-medium text-gray-900 dark:text-white">
                      {item.count}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6">
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Recent Projects</h3>
          {projects && projects.length > 0 ? (
            <ul className="space-y-3">
              {projects.slice(0, 5).map((project) => (
                <li key={project.id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{project.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{project.description}</p>
                  </div>
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">No projects yet. Create your first project to get started.</p>
          )}
        </div>

      </div>
    </div>
  );
};

export default Dashboard;