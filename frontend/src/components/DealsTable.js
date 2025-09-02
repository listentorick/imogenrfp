import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  PlusIcon, 
  MagnifyingGlassIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon,
  TrashIcon,
  PencilIcon
} from '@heroicons/react/24/outline';
import { getDeals, deleteDeal } from '../utils/api';

const DealsTable = ({ projectId, onCreateDeal, showHeader = true }) => {
  const navigate = useNavigate();
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  
  const itemsPerPage = 10;

  const statusOptions = [
    { value: 'all', label: 'All Statuses' },
    { value: 'prospect', label: 'Prospect' },
    { value: 'proposal', label: 'Proposal' },
    { value: 'negotiation', label: 'Negotiation' },
    { value: 'closed_won', label: 'Closed Won' },
    { value: 'closed_lost', label: 'Closed Lost' }
  ];

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

  const handleDeleteDeal = async (dealId, e) => {
    e.stopPropagation();
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

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Filter and search deals
  const filteredDeals = useMemo(() => {
    let filtered = deals;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(deal => 
        deal.name.toLowerCase().includes(query) ||
        deal.company.toLowerCase().includes(query) ||
        (deal.description && deal.description.toLowerCase().includes(query))
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(deal => deal.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];

      // Handle null/undefined values
      if (aValue === null || aValue === undefined) aValue = '';
      if (bValue === null || bValue === undefined) bValue = '';

      // Handle different data types
      if (sortField === 'value') {
        aValue = parseFloat(aValue) || 0;
        bValue = parseFloat(bValue) || 0;
      } else if (sortField === 'created_at' || sortField === 'expected_close_date') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      } else {
        aValue = aValue.toString().toLowerCase();
        bValue = bValue.toString().toLowerCase();
      }

      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [deals, searchQuery, statusFilter, sortField, sortDirection]);

  // Pagination
  const totalPages = Math.ceil(filteredDeals.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedDeals = filteredDeals.slice(startIndex, startIndex + itemsPerPage);

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, statusFilter]);

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
    if (!value) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString();
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return null;
    return (
      <span className="ml-1">
        {sortDirection === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center py-8">Loading deals...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center py-8 text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Header with search and filters */}
      <div className="p-6 border-b border-gray-200">
        {showHeader && (
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Deals</h3>
            <button
              onClick={onCreateDeal}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              New Deal
            </button>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <input
                type="text"
                placeholder="Search deals by name, company, or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
          </div>

          {/* Status Filter */}
          <div className="w-full sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {statusOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Results summary */}
        <div className="mt-4 text-sm text-gray-600">
          Showing {paginatedDeals.length} of {filteredDeals.length} deals
        </div>
      </div>

      {/* Table */}
      {filteredDeals.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500">
            {deals.length === 0 ? (
              <>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No deals yet</h3>
                <p className="mb-4">Get started by creating your first deal.</p>
                <button
                  onClick={onCreateDeal}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  New Deal
                </button>
              </>
            ) : (
              <>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No matching deals</h3>
                <p>Try adjusting your search or filter criteria.</p>
              </>
            )}
          </div>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('name')}
                  >
                    Name <SortIcon field="name" />
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('company')}
                  >
                    Company <SortIcon field="company" />
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('value')}
                  >
                    Value <SortIcon field="value" />
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('status')}
                  >
                    Status <SortIcon field="status" />
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('expected_close_date')}
                  >
                    Expected Close <SortIcon field="expected_close_date" />
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('created_at')}
                  >
                    Created <SortIcon field="created_at" />
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedDeals.map((deal) => (
                  <tr 
                    key={deal.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/deals/${deal.id}`)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{deal.name}</div>
                      {deal.description && (
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {deal.description}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{deal.company}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{formatCurrency(deal.value)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(deal.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{formatDate(deal.expected_close_date)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{formatDate(deal.created_at)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/deals/${deal.id}`);
                        }}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteDeal(deal.id, e)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Page {currentPage} of {totalPages}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeftIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRightIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default DealsTable;