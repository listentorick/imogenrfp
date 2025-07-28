import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';

const ThemeToggle = () => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
      aria-label="Toggle theme"
    >
      {isDark ? (
        <SunIcon className="h-5 w-5 text-gray-300" />
      ) : (
        <MoonIcon className="h-5 w-5 text-gray-300" />
      )}
    </button>
  );
};

export default ThemeToggle;