import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  PencilIcon, 
  CurrencyDollarIcon, 
  BuildingOfficeIcon,
  CalendarIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { getDeal, updateDeal, deleteDeal } from '../utils/api';

const DealDetail = () => {
  const { dealId } = useParams();
  const navigate = useNavigate();
  const [deal, setDeal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});

  const statusOptions = [
    { value: 'prospect', label: 'Prospect', color: 'bg-gray-100 text-gray-800' },
    { value: 'proposal', label: 'Proposal', color: 'bg-blue-100 text-blue-800' },
    { value: 'negotiation', label: 'Negotiation', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'closed_won', label: 'Closed Won', color: 'bg-green-100 text-green-800' },
    { value: 'closed_lost', label: 'Closed Lost', color: 'bg-red-100 text-red-800' }
  ];

  useEffect(() => {
    loadDeal();
  }, [dealId]);

  const loadDeal = async () => {
    try {
      setLoading(true);
      const data = await getDeal(dealId);
      setDeal(data);
      setEditData(data);
    } catch (err) {
      setError('Failed to load deal');
      console.error('Error loading deal:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditData(deal);
  };

  const handleSaveEdit = async () => {
    try {
      const updatedDeal = await updateDeal(dealId, {
        name: editData.name,
        company: editData.company,
        value: editData.value ? parseFloat(editData.value) : null,
        status: editData.status,
        description: editData.description,
        expected_close_date: editData.expected_close_date || null
      });
      setDeal(updatedDeal);
      setIsEditing(false);
    } catch (err) {
      alert('Failed to update deal');
      console.error('Error updating deal:', err);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this deal?')) {
      try {
        await deleteDeal(dealId);
        navigate(`/projects/${deal.project_id}`);
      } catch (err) {
        alert('Failed to delete deal');
        console.error('Error deleting deal:', err);
      }
    }
  };

  const getStatusBadge = (status) => {
    const config = statusOptions.find(opt => opt.value === status) || statusOptions[0];
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatCurrency = (value) => {
    if (!value) return 'Not specified';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="text-gray-600">Loading deal...</div>
      </div>
    );
  }

  if (error || !deal) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Deal not found</h3>
        <button
          onClick={() => navigate(-1)}
          className="text-blue-600 hover:text-blue-800"
        >
          Go back
        </button>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(`/projects/${deal.project_id}`)}
          className="flex items-center text-blue-600 hover:text-blue-800 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Back to Project
        </button>
        
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              {isEditing ? (
                <input
                  type="text"
                  value={editData.name}
                  onChange={(e) => setEditData(prev => ({ ...prev, name: e.target.value }))}
                  className="text-2xl font-bold text-gray-900 border-b-2 border-blue-500 bg-transparent focus:outline-none"
                />
              ) : (
                <h1 className="text-2xl font-bold text-gray-900">{deal.name}</h1>
              )}
              <div className="flex items-center space-x-4 mt-2">
                {getStatusBadge(isEditing ? editData.status : deal.status)}
                <span className="text-sm text-gray-500">
                  Created {new Date(deal.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            
            <div className="flex space-x-2">
              {isEditing ? (
                <>
                  <button
                    onClick={handleSaveEdit}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Save
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
                  >
                    Delete
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Deal Information */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Deal Information</h2>
          
          <div className="space-y-4">
            <div className="flex items-center">
              <BuildingOfficeIcon className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <div className="text-sm text-gray-500">Company</div>
                {isEditing ? (
                  <input
                    type="text"
                    value={editData.company}
                    onChange={(e) => setEditData(prev => ({ ...prev, company: e.target.value }))}
                    className="font-medium text-gray-900 border-b border-gray-300 bg-transparent focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <div className="font-medium text-gray-900">{deal.company}</div>
                )}
              </div>
            </div>

            <div className="flex items-center">
              <CurrencyDollarIcon className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <div className="text-sm text-gray-500">Deal Value</div>
                {isEditing ? (
                  <input
                    type="number"
                    value={editData.value || ''}
                    onChange={(e) => setEditData(prev => ({ ...prev, value: e.target.value }))}
                    className="font-medium text-gray-900 border-b border-gray-300 bg-transparent focus:outline-none focus:border-blue-500"
                    placeholder="0.00"
                  />
                ) : (
                  <div className="font-medium text-gray-900">{formatCurrency(deal.value)}</div>
                )}
              </div>
            </div>

            <div className="flex items-center">
              <CalendarIcon className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <div className="text-sm text-gray-500">Expected Close Date</div>
                {isEditing ? (
                  <input
                    type="date"
                    value={editData.expected_close_date || ''}
                    onChange={(e) => setEditData(prev => ({ ...prev, expected_close_date: e.target.value }))}
                    className="font-medium text-gray-900 border-b border-gray-300 bg-transparent focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <div className="font-medium text-gray-900">
                    {deal.expected_close_date 
                      ? new Date(deal.expected_close_date).toLocaleDateString()
                      : 'Not specified'
                    }
                  </div>
                )}
              </div>
            </div>

            {isEditing && (
              <div className="flex items-start">
                <div className="h-5 w-5 text-gray-400 mr-3 mt-1">Status</div>
                <div>
                  <div className="text-sm text-gray-500">Status</div>
                  <select
                    value={editData.status}
                    onChange={(e) => setEditData(prev => ({ ...prev, status: e.target.value }))}
                    className="font-medium text-gray-900 border-b border-gray-300 bg-transparent focus:outline-none focus:border-blue-500"
                  >
                    {statusOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Description</h2>
          {isEditing ? (
            <textarea
              value={editData.description || ''}
              onChange={(e) => setEditData(prev => ({ ...prev, description: e.target.value }))}
              rows={6}
              className="w-full text-gray-700 border border-gray-300 rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter deal description..."
            />
          ) : (
            <div className="text-gray-700">
              {deal.description || (
                <span className="text-gray-400 italic">No description provided</span>
              )}
            </div>
          )}
        </div>
      </div>

    </div>
  );
};

export default DealDetail;