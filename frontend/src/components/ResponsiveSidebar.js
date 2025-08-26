import React, { createContext, useContext, useState, useEffect } from 'react';
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
import { cn } from '../lib/utils';

// Sidebar Context
const SidebarContext = createContext();

const SidebarProvider = ({ defaultOpen = true, open: openProp, onOpenChange, children }) => {
  const [_open, _setOpen] = useState(defaultOpen);
  const [isMobile, setIsMobile] = useState(false);
  
  const open = openProp ?? _open;
  const setOpen = onOpenChange ?? _setOpen;

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    if (!isMobile || !open) return;
    
    const handleClick = (e) => {
      if (!e.target.closest('[data-sidebar]')) {
        setOpen(false);
      }
    };

    // Add slight delay to prevent immediate closing
    const timer = setTimeout(() => {
      document.addEventListener('click', handleClick);
    }, 100);

    return () => {
      clearTimeout(timer);
      document.removeEventListener('click', handleClick);
    };
  }, [isMobile, open, setOpen]);

  const contextValue = {
    open,
    setOpen,
    isMobile
  };

  return (
    <SidebarContext.Provider value={contextValue}>
      <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
        {children}
      </div>
    </SidebarContext.Provider>
  );
};


const SidebarTrigger = ({ className, ...props }) => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('SidebarTrigger must be used within a SidebarProvider');
  }
  const { setOpen, isMobile } = context;
  
  return (
    <button
      onClick={() => setOpen(prev => !prev)}
      className={cn(
        "inline-flex items-center justify-center rounded-md p-2 text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500",
        isMobile ? "md:hidden" : "hidden",
        className
      )}
      {...props}
    >
      <Bars3Icon className="h-6 w-6" />
      <span className="sr-only">Open sidebar</span>
    </button>
  );
};

const Sidebar = ({ children, className, ...props }) => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('Sidebar must be used within a SidebarProvider');
  }
  const { open, isMobile } = context;
  
  return (
    <>
      {/* Mobile backdrop */}
      {isMobile && open && (
        <div className="fixed inset-0 z-40 bg-black bg-opacity-50 md:hidden" />
      )}
      
      {/* Sidebar */}
      <div
        data-sidebar
        className={cn(
          "flex flex-col bg-gray-800 shadow-lg transition-all duration-300 ease-in-out",
          // Desktop: always visible, collapsible width
          "hidden md:flex",
          open ? "md:w-64" : "md:w-16",
          // Mobile: overlay when open
          isMobile && open && "fixed inset-y-0 left-0 z-50 flex w-64",
          className
        )}
        {...props}
      >
        {children}
      </div>
    </>
  );
};

const SidebarHeader = ({ children, className, ...props }) => {
  return (
    <div className={cn("p-6", className)} {...props}>
      {children}
    </div>
  );
};

const SidebarContent = ({ children, className, ...props }) => {
  return (
    <div className={cn("flex-1 overflow-y-auto", className)} {...props}>
      {children}
    </div>
  );
};

const SidebarNav = ({ children, className, ...props }) => {
  return (
    <nav className={cn("mt-6 flex-1", className)} {...props}>
      {children}
    </nav>
  );
};

const SidebarNavItem = ({ href, icon: Icon, children, className, ...props }) => {
  const location = useLocation();
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('SidebarNavItem must be used within a SidebarProvider');
  }
  const { open, setOpen, isMobile } = context;
  const isActive = location.pathname === href;

  const handleClick = () => {
    if (isMobile) {
      setOpen(false);
    }
  };

  return (
    <Link
      to={href}
      onClick={handleClick}
      className={cn(
        "flex items-center px-6 py-3 text-sm font-medium transition-all duration-200",
        isActive
          ? "bg-blue-900/50 border-r-2 border-blue-500 text-blue-300"
          : "text-gray-300 hover:bg-gray-700",
        !open && "md:px-3 md:justify-center",
        className
      )}
      title={!open ? children : undefined}
      {...props}
    >
      <Icon className={cn("h-5 w-5", open ? "mr-3" : "md:mr-0")} />
      <span className={cn("transition-opacity duration-200", !open && "md:hidden")}>
        {children}
      </span>
    </Link>
  );
};

const SidebarFooter = ({ children, className, ...props }) => {
  return (
    <div className={cn("p-6 mt-auto", className)} {...props}>
      {children}
    </div>
  );
};

const ResponsiveSidebar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  // Get context with error handling
  const context = useContext(SidebarContext);
  if (!context) {
    console.error('ResponsiveSidebar: No SidebarContext found');
    return <div>Sidebar context error</div>;
  }
  
  const { open, setOpen } = context;

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

  const handleMobileClose = () => {
    setOpen(false);
  };

  return (
    <Sidebar>
      {/* Mobile close button */}
      <div className="md:hidden absolute top-4 right-4 z-10">
        <button
          onClick={handleMobileClose}
          className="p-2 text-gray-400 hover:text-gray-200"
        >
          <XMarkIcon className="h-6 w-6" />
        </button>
      </div>

      <SidebarHeader>
        <div className={cn("flex", !open && "md:justify-center")}>
          <img 
            src="/images/imogenrfplogo.png" 
            alt="ImogenRFP" 
            className={cn(
              "h-12 w-auto mb-2 transition-all duration-200",
              !open && "md:h-8"
            )}
          />
        </div>
        {open && (
          <p className="text-sm text-gray-300 mt-1 transition-opacity duration-200">
            {user?.email}
          </p>
        )}
      </SidebarHeader>
      
      <SidebarContent>
        <SidebarNav>
          {navigation.map((item) => (
            <SidebarNavItem
              key={item.name}
              href={item.href}
              icon={item.icon}
            >
              {item.name}
            </SidebarNavItem>
          ))}
        </SidebarNav>
      </SidebarContent>

      <SidebarFooter>
        <button
          onClick={handleLogout}
          className={cn(
            "flex items-center w-full px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-700 rounded-md transition-all duration-200",
            !open && "md:justify-center"
          )}
          title={!open ? "Sign out" : undefined}
        >
          <ArrowRightOnRectangleIcon className={cn("h-5 w-5", open ? "mr-3" : "md:mr-0")} />
          <span className={cn("transition-opacity duration-200", !open && "md:hidden")}>
            Sign out
          </span>
        </button>
      </SidebarFooter>
    </Sidebar>
  );
};

export { SidebarProvider, SidebarTrigger, ResponsiveSidebar };