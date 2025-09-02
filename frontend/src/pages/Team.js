import React, { useState, useEffect } from 'react';
import { PlusIcon, EnvelopeIcon, UserCircleIcon } from '@heroicons/react/24/outline';
import { api } from '../utils/api';

const Team = () => {
  const [users, setUsers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'

  const fetchTeamData = async () => {
    try {
      // Fetch tenant users
      const usersResponse = await api.get('/tenants/users');
      setUsers(usersResponse.data);

      // Fetch pending invitations
      const invitationsResponse = await api.get('/tenants/invitations');
      setInvitations(invitationsResponse.data);
    } catch (error) {
      console.error('Error fetching team data:', error);
    }
  };

  const sendInvitation = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');
    
    try {
      const response = await api.post('/tenants/invitations', { email: inviteEmail });
      
      setMessage('Invitation sent successfully! The user will receive an email to join your team.');
      setMessageType('success');
      setInviteEmail('');
      setShowInviteForm(false);
      fetchTeamData(); // Refresh the data
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Error sending invitation';
      setMessage(errorMessage);
      setMessageType('error');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  useEffect(() => {
    fetchTeamData();
  }, []);

  // Clear message after 5 seconds
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage('');
        setMessageType('');
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Team Management</h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Manage your team members and invite new users to join your organization
            </p>
          </div>
          <button
            onClick={() => setShowInviteForm(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Invite User
          </button>
        </div>
      </div>

      {/* Success/Error Message */}
      {message && (
        <div className={`mb-6 p-4 rounded-md ${
          messageType === 'success' 
            ? 'bg-green-50 border border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200'
            : 'bg-red-50 border border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200'
        }`}>
          {message}
        </div>
      )}

      {/* Invite User Form */}
      {showInviteForm && (
        <div className="mb-8 bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Invite New Member</h2>
          </div>
          <form onSubmit={sendInvitation} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={isLoading}
                className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium rounded-md transition-colors"
              >
                <EnvelopeIcon className="h-4 w-4 mr-2" />
                {isLoading ? 'Sending...' : 'Send Invitation'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowInviteForm(false);
                  setInviteEmail('');
                  setMessage('');
                }}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Team Members */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Team Members</h2>
        </div>
        
        <div className="overflow-hidden">
          {users.length === 0 ? (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400">
              No team members found. Start by inviting users to join your team.
            </div>
          ) : (
            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
              {users.map((user) => (
                <li key={user.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <UserCircleIcon className="h-10 w-10 text-gray-400 dark:text-gray-500" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {user.first_name} {user.last_name}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                        {user.email}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      Joined {formatDate(user.created_at)}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Pending Invitations */}
      {invitations.length > 0 && (
        <div className="mt-8 bg-white dark:bg-gray-800 shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Pending Invitations</h2>
          </div>
          
          <div className="overflow-hidden">
            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
              {invitations.map((invitation) => (
                <li key={invitation.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="h-10 w-10 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center">
                        <EnvelopeIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {invitation.email}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Invited {formatDate(invitation.created_at)} • Expires {formatDate(invitation.expires_at)}
                        </p>
                      </div>
                    </div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
                      Pending
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default Team;