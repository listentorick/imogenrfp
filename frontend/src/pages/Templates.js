import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../utils/api';
import { PlusIcon, EyeIcon } from '@heroicons/react/24/outline';

const Templates = () => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    template_content: '',
    template_type: 'html',
    is_default: false
  });

  const queryClient = useQueryClient();

  const { data: templates, isLoading } = useQuery(
    'templates',
    () => api.get('/templates/').then(res => res.data)
  );

  const createTemplateMutation = useMutation(
    (templateData) => api.post('/templates/', templateData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('templates');
        setShowCreateForm(false);
        setFormData({
          name: '',
          template_content: '',
          template_type: 'html',
          is_default: false
        });
      }
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    createTemplateMutation.mutate(formData);
  };

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value
    });
  };

  const loadDefaultTemplate = (type) => {
    const defaultHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ rfp.title }} - Response</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
        .header { background-color: {{ branding.primary_color or '#007bff' }}; color: white; padding: 20px; margin-bottom: 30px; }
        .question { font-weight: bold; color: {{ branding.primary_color or '#007bff' }}; margin-bottom: 10px; }
        .answer { margin-left: 20px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ rfp.title }}</h1>
        {% if rfp.client_name %}<p>Client: {{ rfp.client_name }}</p>{% endif %}
    </div>
    {% for question in rfp.questions %}
    <div class="question">{{ loop.index }}. {{ question.question_text }}</div>
    <div class="answer">{{ question.generated_answer or 'Answer pending' }}</div>
    {% endfor %}
</body>
</html>`;

    const defaultMarkdown = `# {{ rfp.title }}

{% if rfp.client_name %}**Client:** {{ rfp.client_name }}{% endif %}
**Generated:** {{ current_date }}

---

{% for question in rfp.questions %}
## {{ loop.index }}. {{ question.question_text }}

{{ question.generated_answer or '*Answer pending*' }}

---
{% endfor %}`;

    setFormData({
      ...formData,
      template_content: type === 'html' ? defaultHTML : defaultMarkdown,
      template_type: type
    });
  };

  if (isLoading) {
    return <div className="flex justify-center py-8">Loading...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Templates</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage output templates for RFP responses with custom branding
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          New Template
        </button>
      </div>

      {showCreateForm && (
        <div className="mb-8 bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Template</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Name
                </label>
                <input
                  type="text"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter template name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Type
                </label>
                <select
                  name="template_type"
                  value={formData.template_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="html">HTML</option>
                  <option value="markdown">Markdown</option>
                </select>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Template Content
                </label>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={() => loadDefaultTemplate('html')}
                    className="text-xs bg-gray-200 px-2 py-1 rounded hover:bg-gray-300"
                  >
                    Load HTML Template
                  </button>
                  <button
                    type="button"
                    onClick={() => loadDefaultTemplate('markdown')}
                    className="text-xs bg-gray-200 px-2 py-1 rounded hover:bg-gray-300"
                  >
                    Load Markdown Template
                  </button>
                </div>
              </div>
              <textarea
                name="template_content"
                required
                value={formData.template_content}
                onChange={handleChange}
                rows={12}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                placeholder="Enter your template content using Jinja2 syntax"
              />
              <p className="text-xs text-gray-500 mt-1">
                Use Jinja2 template syntax. Available variables: rfp, branding, current_date, generated_at
              </p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                name="is_default"
                checked={formData.is_default}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-700">
                Set as default template
              </label>
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
                disabled={createTemplateMutation.isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {createTemplateMutation.isLoading ? 'Creating...' : 'Create Template'}
              </button>
            </div>
          </form>
        </div>
      )}

      {previewTemplate && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Template Preview</h3>
              <button
                onClick={() => setPreviewTemplate(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="bg-gray-100 p-4 rounded-md max-h-96 overflow-auto">
              <pre className="text-sm font-mono whitespace-pre-wrap">
                {previewTemplate.template_content}
              </pre>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          {templates && templates.length > 0 ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {templates.map((template) => (
                <div key={template.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-1">
                        {template.name}
                      </h3>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          template.template_type === 'html' 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {template.template_type.toUpperCase()}
                        </span>
                        {template.is_default && (
                          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                            Default
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => setPreviewTemplate(template)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <EyeIcon className="h-5 w-5" />
                    </button>
                  </div>
                  <div className="text-sm text-gray-500">
                    Created {new Date(template.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <h3 className="text-lg font-medium text-gray-900 mb-2">No templates yet</h3>
              <p className="text-gray-600 mb-4">Create your first template to customize RFP output formats</p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Create Template
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Templates;