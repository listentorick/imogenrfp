import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../utils/api';
import { 
  HomeIcon,
  FolderIcon,
  DocumentDuplicateIcon,
  ArrowRightOnRectangleIcon,
  CogIcon,
  Bars3Icon,
  XMarkIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  UsersIcon,
  BriefcaseIcon,
  BookOpenIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';

const SimpleSidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(false);
  const [projectsExpanded, setProjectsExpanded] = useState(true);

  // Fetch projects for navigation
  const { data: projects } = useQuery(
    'projects',
    () => api.get('/projects/').then(res => res.data),
    { staleTime: 5 * 60 * 1000 } // Cache for 5 minutes
  );

  // Fetch tenant information for default project
  const { data: tenant } = useQuery(
    'tenant',
    () => api.get('/tenants/me').then(res => res.data),
    { staleTime: 5 * 60 * 1000 } // Cache for 5 minutes
  );

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { 
      name: 'Deals', 
      href: tenant?.default_project_id ? `/projects/${tenant.default_project_id}/deals` : '/projects', 
      icon: BriefcaseIcon 
    },
    { 
      name: 'Knowledge', 
      href: tenant?.default_project_id ? `/projects/${tenant.default_project_id}/knowledge` : '/projects', 
      icon: BookOpenIcon 
    },
    { 
      name: 'Ask Imogen', 
      href: tenant?.default_project_id ? `/projects/${tenant.default_project_id}/ask-imogen` : '/projects', 
      icon: ChatBubbleLeftRightIcon 
    },
    { name: 'Templates', href: '/templates', icon: DocumentDuplicateIcon },
    { name: 'Team', href: '/team', icon: UsersIcon },
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
          {/* Dashboard */}
          <Link
            to="/"
            onClick={handleNavClick}
            className={`
              flex items-center py-3 text-sm font-medium transition-all duration-200
              ${location.pathname === '/'
                ? 'bg-blue-900/50 border-r-2 border-blue-500 text-blue-300'
                : 'text-gray-300 hover:bg-gray-700'
              }
              ${isOpen || isMobile ? 'px-6' : 'px-3 justify-center'}
            `}
            title={!isOpen && !isMobile ? 'Dashboard' : undefined}
          >
            <HomeIcon className={`h-5 w-5 ${(isOpen || isMobile) ? 'mr-3' : ''}`} />
            {(isOpen || isMobile) && <span>Dashboard</span>}
          </Link>

          {/* Other Navigation Items - first 3 items (Deals, Knowledge, Ask Imogen) */}
          {navigation.slice(1, 4).map((item) => {
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

          {/* Projects Section - moved after Ask Imogen */}
          <div className="mt-2">
            {/* Main Projects Item */}
            <div className="flex">
              <Link
                to="/projects"
                onClick={handleNavClick}
                className={`
                  flex items-center flex-1 py-3 text-sm font-medium transition-all duration-200
                  ${location.pathname === '/projects'
                    ? 'bg-blue-900/50 border-r-2 border-blue-500 text-blue-300'
                    : 'text-gray-300 hover:bg-gray-700'
                  }
                  ${isOpen || isMobile ? 'pl-6 pr-2' : 'px-3 justify-center'}
                `}
                title={!isOpen && !isMobile ? 'Partitions' : undefined}
              >
                <FolderIcon className={`h-5 w-5 ${(isOpen || isMobile) ? 'mr-3' : ''}`} />
                {(isOpen || isMobile) && <span>Partitions</span>}
              </Link>
              
              {/* Expand/Collapse Button */}
              {(isOpen || isMobile) && (
                <button
                  onClick={() => setProjectsExpanded(!projectsExpanded)}
                  className="px-2 py-3 text-gray-300 hover:text-gray-100"
                >
                  {projectsExpanded ? (
                    <ChevronDownIcon className="h-4 w-4" />
                  ) : (
                    <ChevronRightIcon className="h-4 w-4" />
                  )}
                </button>
              )}
            </div>

            {/* Project List */}
            {projectsExpanded && (isOpen || isMobile) && projects && projects.length > 0 && (
              <div className="ml-8">
                {projects.map((project) => {
                  const isProjectActive = location.pathname.startsWith(`/projects/${project.id}`);
                  return (
                    <Link
                      key={project.id}
                      to={`/projects/${project.id}/deals`}
                      onClick={handleNavClick}
                      className={`
                        flex items-center py-2 px-4 text-sm transition-all duration-200
                        ${isProjectActive
                          ? 'bg-blue-900/30 text-blue-300'
                          : 'text-gray-400 hover:bg-gray-700 hover:text-gray-300'
                        }
                      `}
                    >
                      <span className="truncate">{project.name}</span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>

          {/* Remaining Navigation Items - Templates, Team, Settings */}
          {navigation.slice(4).map((item) => {
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