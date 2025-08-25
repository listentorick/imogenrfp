import React, { useState, useEffect } from 'react';
import { 
  ClockIcon,
  UserIcon,
  CpuChipIcon,
  PencilIcon,
  PlusIcon
} from '@heroicons/react/24/outline';

// Advanced diff function to create inline diff with additions and deletions
const getInlineDiff = (current, previous) => {
  if (!previous) return [{ type: 'added', text: current }];
  if (!current) return [{ type: 'deleted', text: previous }];
  if (current === previous) return [{ type: 'unchanged', text: current }];
  
  // Split into words for word-level diffing
  const currentWords = current.split(/(\s+)/);
  const previousWords = previous.split(/(\s+)/);
  
  // Simple LCS-based diff algorithm
  const dp = Array(previousWords.length + 1).fill(null).map(() => 
    Array(currentWords.length + 1).fill(0)
  );
  
  // Fill the DP table
  for (let i = 1; i <= previousWords.length; i++) {
    for (let j = 1; j <= currentWords.length; j++) {
      if (previousWords[i - 1] === currentWords[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  
  // Backtrack to build the diff
  const diff = [];
  let i = previousWords.length;
  let j = currentWords.length;
  
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && previousWords[i - 1] === currentWords[j - 1]) {
      diff.unshift({ type: 'unchanged', text: previousWords[i - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      diff.unshift({ type: 'added', text: currentWords[j - 1] });
      j--;
    } else if (i > 0) {
      diff.unshift({ type: 'deleted', text: previousWords[i - 1] });
      i--;
    }
  }
  
  return diff;
};

const AuditHistoryModal = ({ questionId, isVisible, onClose }) => {
  const [auditHistory, setAuditHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isVisible && questionId) {
      loadAuditHistory();
    }
  }, [isVisible, questionId]);

  const loadAuditHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/questions/${questionId}/audit-history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to load audit history');
      }

      const data = await response.json();
      setAuditHistory(data);
    } catch (error) {
      console.error('Error loading audit history:', error);
      setError('Failed to load audit history');
    } finally {
      setLoading(false);
    }
  };

  const getChangeIcon = (changeSource) => {
    switch (changeSource) {
      case 'ai_initial':
        return <CpuChipIcon className="h-4 w-4 text-blue-500" />;
      case 'user_edit':
        return <PencilIcon className="h-4 w-4 text-green-500" />;
      case 'user_create':
        return <PlusIcon className="h-4 w-4 text-green-500" />;
      default:
        return <UserIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const getChangeDescription = (changeSource, changeType) => {
    if (changeSource === 'ai_initial') return 'Generated answer';
    if (changeSource === 'user_create') return 'Created answer';
    if (changeSource === 'user_edit') return 'Edited answer';
    return 'Modified answer';
  };

  if (!isVisible) return null;

  return (
    <>
      {/* Modal backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />
      
      {/* Modal content */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
          <div className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <ClockIcon className="h-5 w-5 mr-2" />
                Edit History
              </h2>
              <button 
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-2xl font-light"
              >
                ×
              </button>
            </div>

            {/* Content */}
            <div className="max-h-96 overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">Loading...</span>
          </div>
        )}

        {error && (
          <div className="text-red-600 dark:text-red-400 text-sm py-2">
            {error}
          </div>
        )}

        {!loading && !error && auditHistory.length === 0 && (
          <div className="text-gray-500 dark:text-gray-400 text-sm py-2">
            No edit history available
          </div>
        )}

        {!loading && !error && auditHistory.length > 0 && (
          <div className="space-y-4">
            {auditHistory.map((record, index) => {
              const previousRecord = auditHistory[index + 1];
              const diffSegments = previousRecord?.answer_text 
                ? getInlineDiff(record.answer_text, previousRecord.answer_text)
                : [{ type: 'added', text: record.answer_text }];
              
              return (
                <div key={record.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-3">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-0.5">
                      {getChangeIcon(record.change_source)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {record.editor_name}
                        </p>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {record.time_ago}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                        {getChangeDescription(record.change_source, record.change_type)}
                      </p>
                      {record.editor_email && record.editor_email !== record.editor_name && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                          {record.editor_email}
                        </p>
                      )}
                      
                      {/* Answer content with inline diff highlighting */}
                      {record.answer_text && (
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                              {previousRecord?.answer_text ? 'Changes Made' : 'Content'}
                            </span>
                            {previousRecord?.answer_text && (
                              <span className="text-xs text-blue-600 dark:text-blue-400">
                                Modified
                              </span>
                            )}
                          </div>
                          <div className="text-gray-900 dark:text-white leading-relaxed">
                            {diffSegments.map((segment, segmentIndex) => {
                              if (segment.type === 'unchanged') {
                                return (
                                  <span key={segmentIndex} className="whitespace-pre-wrap">
                                    {segment.text}
                                  </span>
                                );
                              } else if (segment.type === 'added') {
                                return (
                                  <span 
                                    key={segmentIndex} 
                                    className="bg-green-200 dark:bg-green-800 text-green-900 dark:text-green-100 whitespace-pre-wrap"
                                  >
                                    {segment.text}
                                  </span>
                                );
                              } else if (segment.type === 'deleted') {
                                return (
                                  <span 
                                    key={segmentIndex} 
                                    className="bg-red-200 dark:bg-red-800 text-red-900 dark:text-red-100 line-through whitespace-pre-wrap opacity-75"
                                  >
                                    {segment.text}
                                  </span>
                                );
                              }
                              return null;
                            })}
                          </div>
                        </div>
                      )}
                      
                      {record.chromadb_relevance_score && (
                        <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                          AI Confidence: {Math.round(record.chromadb_relevance_score)}%
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AuditHistoryModal;