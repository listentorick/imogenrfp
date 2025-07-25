import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../utils/api';
import { PlusIcon, SparklesIcon, DocumentIcon } from '@heroicons/react/24/outline';

const RFPRequests = () => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedRFP, setSelectedRFP] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    client_name: '',
    due_date: '',
    project_id: '',
    questions: [{ question_text: '' }]
  });

  const queryClient = useQueryClient();

  const { data: projects } = useQuery(
    'projects',
    () => api.get('/projects/').then(res => res.data)
  );

  const { data: rfpRequests, isLoading } = useQuery(
    'rfp-requests',
    () => api.get('/rfp-requests/').then(res => res.data)
  );

  const createRFPMutation = useMutation(
    (rfpData) => api.post('/rfp-requests/', rfpData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('rfp-requests');
        setShowCreateForm(false);
        setFormData({
          title: '',
          client_name: '',
          due_date: '',
          project_id: '',
          questions: [{ question_text: '' }]
        });
      }
    }
  );

  const generateAnswersMutation = useMutation(
    (rfpId) => api.post(`/rfp-requests/${rfpId}/generate-answers`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('rfp-requests');
        alert('Answers generated successfully!');
      }
    }
  );

  const renderRFPMutation = useMutation(
    ({ rfpId, templateId, brandingData }) => 
      api.post(`/rfp-requests/${rfpId}/render`, { template_id: templateId, branding_data: brandingData }),
    {
      onSuccess: (data) => {
        const blob = new Blob([data.data.rendered_content], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rfp-response-${Date.now()}.html`;
        a.click();
        URL.revokeObjectURL(url);
      }
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      questions: formData.questions.filter(q => q.question_text.trim() !== '')
    };
    createRFPMutation.mutate(submitData);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const addQuestion = () => {
    setFormData({
      ...formData,
      questions: [...formData.questions, { question_text: '' }]
    });
  };

  const updateQuestion = (index, value) => {
    const newQuestions = [...formData.questions];
    newQuestions[index].question_text = value;
    setFormData({
      ...formData,
      questions: newQuestions
    });
  };

  const removeQuestion = (index) => {
    const newQuestions = formData.questions.filter((_, i) => i !== index);
    setFormData({
      ...formData,
      questions: newQuestions
    });
  };

  if (isLoading) {
    return <div className="flex justify-center py-8">Loading...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">RFP Requests</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage and generate responses to RFP requests
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          New RFP
        </button>
      </div>

      {showCreateForm && (
        <div className="mb-8 bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create New RFP Request</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  RFP Title *
                </label>
                <input
                  type="text"
                  name="title"
                  required
                  value={formData.title}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter RFP title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Client Name
                </label>
                <input
                  type="text"
                  name="client_name"
                  value={formData.client_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter client name"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Due Date
                </label>
                <input
                  type="date"
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Project *
                </label>
                <select
                  name="project_id"
                  required
                  value={formData.project_id}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a project</option>
                  {projects?.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Questions
              </label>
              {formData.questions.map((question, index) => (
                <div key={index} className="flex mb-2">
                  <input
                    type="text"
                    value={question.question_text}
                    onChange={(e) => updateQuestion(index, e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder={`Question ${index + 1}`}
                  />
                  {formData.questions.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeQuestion(index)}
                      className="ml-2 px-3 py-2 text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={addQuestion}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                + Add Question
              </button>
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
                disabled={createRFPMutation.isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {createRFPMutation.isLoading ? 'Creating...' : 'Create RFP'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          {rfpRequests && rfpRequests.length > 0 ? (
            <div className="space-y-6">
              {rfpRequests.map((rfp) => (
                <div key={rfp.id} className="border border-gray-200 rounded-lg p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-1">
                        {rfp.title}
                      </h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        {rfp.client_name && <span>Client: {rfp.client_name}</span>}
                        {rfp.due_date && <span>Due: {new Date(rfp.due_date).toLocaleDateString()}</span>}
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          rfp.status === 'completed' ? 'bg-green-100 text-green-800' :
                          rfp.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {rfp.status}
                        </span>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => generateAnswersMutation.mutate(rfp.id)}
                        disabled={generateAnswersMutation.isLoading}
                        className="flex items-center px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 disabled:opacity-50"
                      >
                        <SparklesIcon className="h-4 w-4 mr-1" />
                        Generate Answers
                      </button>
                      <button
                        onClick={() => renderRFPMutation.mutate({ rfpId: rfp.id })}
                        disabled={renderRFPMutation.isLoading}
                        className="flex items-center px-3 py-2 bg-purple-600 text-white text-sm rounded-md hover:bg-purple-700 disabled:opacity-50"
                      >
                        <DocumentIcon className="h-4 w-4 mr-1" />
                        Export
                      </button>
                    </div>
                  </div>
                  
                  {rfp.questions && rfp.questions.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">
                        Questions ({rfp.questions.length})
                      </h4>
                      <div className="space-y-3">
                        {rfp.questions.slice(0, 3).map((question, index) => (
                          <div key={question.id} className="bg-gray-50 p-3 rounded">
                            <p className="text-sm font-medium text-gray-800">
                              {index + 1}. {question.question_text}
                            </p>
                            {question.generated_answer && (
                              <p className="text-sm text-gray-600 mt-2">
                                Answer: {question.generated_answer.substring(0, 100)}...
                              </p>
                            )}
                          </div>
                        ))}
                        {rfp.questions.length > 3 && (
                          <p className="text-sm text-gray-500">
                            ... and {rfp.questions.length - 3} more questions
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <h3 className="text-lg font-medium text-gray-900 mb-2">No RFP requests yet</h3>
              <p className="text-gray-600 mb-4">Create your first RFP request to get started</p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Create RFP Request
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RFPRequests;