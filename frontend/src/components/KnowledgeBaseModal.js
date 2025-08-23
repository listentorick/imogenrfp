import React, { useState } from 'react';
import { 
  XMarkIcon,
  BookOpenIcon,
  CheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const KnowledgeBaseModal = ({ isOpen, onClose, question, onAddToKnowledgeBase }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !question) return null;

  const handleAddToKnowledgeBase = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      await onAddToKnowledgeBase(question.id);
      
      // Close modal on success
      onClose();
    } catch (error) {
      console.error('Error adding to knowledge base:', error);
      setError(error.message || 'Failed to add to knowledge base');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white dark:bg-gray-800">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <BookOpenIcon className="h-8 w-8 text-blue-500" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Add to Project Knowledge Base
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Save this Q&A pair for future reference in this project
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="mt-6 space-y-6">
          {/* Question Preview */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Question
            </label>
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-gray-900 dark:text-white">
                {question.question_text}
              </p>
            </div>
          </div>

          {/* Answer Preview */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Answer
            </label>
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <p className="text-gray-900 dark:text-white whitespace-pre-wrap">
                {question.answer_text}
              </p>
            </div>
          </div>

          {/* Information */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  About the Project Knowledge Base
                </h4>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  This Q&A pair will be saved to your project's knowledge base and can be used to help answer similar questions in future deals.
                </p>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-red-800 dark:text-red-200">
                    Error
                  </h4>
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-8 flex items-center justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleAddToKnowledgeBase}
            disabled={isLoading || !question.answer_text?.trim()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Adding...
              </>
            ) : (
              <>
                <CheckIcon className="h-4 w-4 mr-2" />
                Add to Knowledge Base
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBaseModal;