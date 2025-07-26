import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon, CurrencyDollarIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';
import { getDeals, deleteDeal } from '../utils/api';

const DealsList = ({ projectId, onCreateDeal }) => {
  const navigate = useNavigate();
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDeals();
  }, [projectId]);

  const loadDeals = async () => {
    try {
      setLoading(true);
      const data = await getDeals(projectId);
      setDeals(data);
    } catch (err) {
      setError('Failed to load deals');
      console.error('Error loading deals:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDeal = async (dealId) => {
    if (window.confirm('Are you sure you want to delete this deal?')) {
      try {
        await deleteDeal(dealId);
        setDeals(deals.filter(deal => deal.id !== dealId));
      } catch (err) {
        alert('Failed to delete deal');
        console.error('Error deleting deal:', err);
      }
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      prospect: { text: 'Prospect', className: 'bg-gray-100 text-gray-800' },
      proposal: { text: 'Proposal', className: 'bg-blue-100 text-blue-800' },
      negotiation: { text: 'Negotiation', className: 'bg-yellow-100 text-yellow-800' },
      closed_won: { text: 'Closed Won', className: 'bg-green-100 text-green-800' },
      closed_lost: { text: 'Closed Lost', className: 'bg-red-100 text-red-800' }
    };

    const config = statusConfig[status] || statusConfig.prospect;
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
        {config.text}
      </span>
    );
  };

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Deals</h3>
        </div>
        <div className="text-center py-4">Loading deals...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Deals</h3>
        </div>
        <div className="text-center py-4 text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Deals</h3>
        <button
          onClick={onCreateDeal}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <PlusIcon className="h-4 w-4 mr-1" />
          New Deal
        </button>
      </div>

      {deals.length === 0 ? (
        <div className="text-center py-8">
          <CurrencyDollarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No deals</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating your first deal.
          </p>
          <div className="mt-6">
            <button
              onClick={onCreateDeal}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              New Deal
            </button>
          </div>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {deals.map((deal) => (
            <div
              key={deal.id}
              onClick={() => navigate(`/deals/${deal.id}`)}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="text-base font-medium text-gray-900 hover:text-blue-600">{deal.name}</h4>
                    {getStatusBadge(deal.status)}
                  </div>
                  <div className="flex items-center text-sm text-gray-600 mb-2">
                    <BuildingOfficeIcon className="h-4 w-4 mr-1" />
                    {deal.company}
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center text-sm text-gray-600">
                      <CurrencyDollarIcon className="h-4 w-4 mr-1" />
                      <span className="font-medium">{formatCurrency(deal.value)}</span>
                    </div>
                    {deal.expected_close_date && (
                      <div className="text-xs text-gray-500">
                        Expected close: {new Date(deal.expected_close_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  {deal.description && (
                    <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                      {deal.description}
                    </p>
                  )}
                </div>
                <div className="flex-shrink-0 ml-4">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteDeal(deal.id);
                    }}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DealsList;