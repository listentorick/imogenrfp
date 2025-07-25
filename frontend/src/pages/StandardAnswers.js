import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../utils/api';
import { PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const StandardAnswers = () => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProject, setSelectedProject] = useState('');
  const [formData, setFormData] = useState({
    question: '',
    answer: '',
    tags: '',
    project_id: ''
  });

  const queryClient = useQueryClient();

  const { data: projects } = useQuery(
    'projects',
    () => api.get('/projects/').then(res => res.data)
  );

  const { data: standardAnswers, isLoading } = useQuery(
    ['standard-answers', selectedProject],
    () => {
      const params = selectedProject ? `?project_id=${selectedProject}` : '';
      return api.get(`/standard-answers/${params}`).then(res => res.data);
    }
  );

  const createAnswerMutation = useMutation(
    (answerData) => api.post('/standard-answers/', answerData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('standard-answers');
        setShowCreateForm(false);
        setFormData({ question: '', answer: '', tags: '', project_id: '' });
      }
    }
  );

  const bulkIndexMutation = useMutation(
    () => api.post('/standard-answers/bulk-index'),
    {
      onSuccess: (data) => {
        alert(`Successfully indexed ${data.data.message}`);
      }
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      tags: formData.tags ? formData.tags.split(',').map(tag => tag.trim()) : [],
      project_id: formData.project_id || null
    };
    createAnswerMutation.mutate(submitData);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const filteredAnswers = standardAnswers?.filter(answer =>
    answer.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
    answer.answer.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (answer.tags && answer.tags.some(tag => 
      tag.toLowerCase().includes(searchTerm.toLowerCase())
    ))
  ) || [];

  if (isLoading) {
    return <div className="flex justify-center py-8">Loading...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Standard Answers</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage your knowledge base for automated RFP responses
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => bulkIndexMutation.mutate()}
            disabled={bulkIndexMutation.isLoading}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {bulkIndexMutation.isLoading ? 'Indexing...' : 'Reindex RAG'}
          </button>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            New Answer
          </button>
        </div>
      </div>

      <div className="mb-6 flex space-x-4">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search questions, answers, or tags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All Projects</option>
          {projects?.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {showCreateForm && (
        <div className="mb-8 bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Standard Answer</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Question
              </label>
              <input
                type="text"
                name="question"
                required
                value={formData.question}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter the question this answer addresses"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Answer
              </label>
              <textarea
                name="answer"
                required
                value={formData.answer}
                onChange={handleChange}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter the standard answer"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project (Optional)
              </label>
              <select
                name="project_id"
                value={formData.project_id}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">General (No specific project)</option>
                {projects?.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                name="tags"
                value={formData.tags}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., technology, security, pricing"
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createAnswerMutation.isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {createAnswerMutation.isLoading ? 'Adding...' : 'Add Answer'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          {filteredAnswers.length > 0 ? (
            <div className="space-y-6">
              {filteredAnswers.map((answer) => (
                <div key={answer.id} className="border-b border-gray-200 pb-6 last:border-b-0">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-medium text-gray-900">
                      {answer.question}
                    </h3>
                    <span className="text-xs text-gray-500">
                      {new Date(answer.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-gray-700 mb-3 whitespace-pre-wrap">
                    {answer.answer}
                  </p>
                  {answer.tags && answer.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {answer.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchTerm ? 'No matching answers found' : 'No standard answers yet'}
              </h3>
              <p className="text-gray-600 mb-4">
                {searchTerm 
                  ? 'Try adjusting your search terms'
                  : 'Create your first standard answer to build your knowledge base'
                }
              </p>
              {!searchTerm && (
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Add Standard Answer
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StandardAnswers;