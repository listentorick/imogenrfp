import React, { useState } from 'react';
import { SimpleSidebar, SidebarToggle } from './SimpleSidebar';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="h-screen bg-gray-100 dark:bg-gray-900 flex">
      <SimpleSidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      
      {/* Main content area */}
      <div className="flex-1 flex flex-col min-h-0 transition-all duration-300">
        {/* Mobile header with menu trigger */}
        <div className="md:hidden bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-2 flex items-center justify-between">
          <SidebarToggle isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">ImogenRFP</h1>
          <div className="w-10" /> {/* Spacer for centering */}
        </div>
        
        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;