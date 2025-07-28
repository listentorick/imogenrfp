import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  HomeIcon,
  FolderIcon,
  DocumentDuplicateIcon,
  ArrowRightOnRectangleIcon,
  CogIcon
} from '@heroicons/react/24/outline';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Projects', href: '/projects', icon: FolderIcon },
    { name: 'Templates', href: '/templates', icon: DocumentDuplicateIcon },
    { name: 'Settings', href: '/settings', icon: CogIcon },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="h-screen bg-gray-100 dark:bg-gray-900 flex">
      {/* Fixed Sidebar */}
      <div className="w-64 bg-gray-800 shadow-lg fixed left-0 top-0 h-full flex flex-col">
        <div className="p-6">
          <img 
            src="/images/imogenrfplogo.png" 
            alt="ImogenRFP" 
            className="h-12 w-auto mb-2"
          />
          <p className="text-sm text-gray-300 mt-1">{user?.email}</p>
        </div>
        
        <nav className="mt-6 flex-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-6 py-3 text-sm font-medium ${
                  isActive
                    ? 'bg-blue-900/50 border-r-2 border-blue-500 text-blue-300'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-6 mt-auto">
          <button
            onClick={handleLogout}
            className="flex items-center w-full px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-700 rounded-md"
          >
            <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5" />
            Sign out
          </button>
        </div>
      </div>

      {/* Main content with left margin for sidebar */}
      <div className="flex-1 ml-64 h-screen overflow-y-auto">
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;