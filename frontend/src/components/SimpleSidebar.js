import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  HomeIcon,
  FolderIcon,
  DocumentDuplicateIcon,
  ArrowRightOnRectangleIcon,
  CogIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const SimpleSidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Projects', href: '/projects', icon: FolderIcon },
    { name: 'Templates', href: '/templates', icon: DocumentDuplicateIcon },
    { name: 'Settings', href: '/settings', icon: CogIcon },
  ];

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    if (!isMobile || !isOpen) return;
    
    const handleClickOutside = (e) => {
      if (!e.target.closest('[data-sidebar="true"]')) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isMobile, isOpen, setIsOpen]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleNavClick = () => {
    if (isMobile) {
      setIsOpen(false);
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isMobile && isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <div
        data-sidebar="true"
        className={`
          flex flex-col bg-gray-800 shadow-lg transition-all duration-300 ease-in-out
          ${isMobile ? 'fixed inset-y-0 left-0 z-50' : 'relative'}
          ${isMobile && !isOpen ? 'hidden' : 'flex'}
          ${!isMobile && !isOpen ? 'w-16' : 'w-64'}
        `}
      >
        {/* Mobile close button */}
        {isMobile && (
          <div className="absolute top-4 right-4 z-10">
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 text-gray-400 hover:text-gray-200 rounded-md"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        )}

        {/* Header */}
        <div className={`p-6 ${!isOpen && !isMobile ? 'p-3 flex justify-center' : ''}`}>
          <img 
            src="/images/imogenrfplogo.png" 
            alt="ImogenRFP" 
            className={`h-12 w-auto mb-2 ${!isOpen && !isMobile ? 'h-8' : ''}`}
          />
          {(isOpen || isMobile) && (
            <p className="text-sm text-gray-300 mt-1">{user?.email}</p>
          )}
        </div>
        
        {/* Navigation */}
        <nav className="mt-6 flex-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={handleNavClick}
                className={`
                  flex items-center py-3 text-sm font-medium transition-all duration-200
                  ${isActive
                    ? 'bg-blue-900/50 border-r-2 border-blue-500 text-blue-300'
                    : 'text-gray-300 hover:bg-gray-700'
                  }
                  ${isOpen || isMobile ? 'px-6' : 'px-3 justify-center'}
                `}
                title={!isOpen && !isMobile ? item.name : undefined}
              >
                <item.icon className={`h-5 w-5 ${(isOpen || isMobile) ? 'mr-3' : ''}`} />
                {(isOpen || isMobile) && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Logout Button */}
        <div className={`p-6 mt-auto ${!isOpen && !isMobile ? 'p-3' : ''}`}>
          <button
            onClick={handleLogout}
            className={`
              flex items-center w-full px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-700 rounded-md transition-all duration-200
              ${!isOpen && !isMobile ? 'justify-center' : ''}
            `}
            title={!isOpen && !isMobile ? "Sign out" : undefined}
          >
            <ArrowRightOnRectangleIcon className={`h-5 w-5 ${(isOpen || isMobile) ? 'mr-3' : ''}`} />
            {(isOpen || isMobile) && <span>Sign out</span>}
          </button>
        </div>
      </div>
    </>
  );
};

const SidebarToggle = ({ isOpen, setIsOpen }) => {
  return (
    <button
      onClick={() => setIsOpen(!isOpen)}
      className="inline-flex items-center justify-center rounded-md p-2 text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 md:hidden"
    >
      <Bars3Icon className="h-6 w-6" />
      <span className="sr-only">Toggle sidebar</span>
    </button>
  );
};

export { SimpleSidebar, SidebarToggle };