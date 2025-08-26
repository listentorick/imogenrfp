import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import AuditHistoryModal from './AuditHistoryModal';
import { 
  ArrowLeftIcon,
  QuestionMarkCircleIcon,
  DocumentTextIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowDownTrayIcon,
  BookOpenIcon,
  PencilIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const DocumentQuestions = () => {
  const { dealId, documentId } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answeredQuestions, setAnsweredQuestions] = useState([]);
  const [partiallyAnsweredQuestions, setPartiallyAnsweredQuestions] = useState([]);
  const [notAnsweredQuestions, setNotAnsweredQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('answered');
  const [editingAnswer, setEditingAnswer] = useState(null);
  const [answerText, setAnswerText] = useState('');
  const [exportStatus, setExportStatus] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [flashingTabs, setFlashingTabs] = useState({
    answered: false,
    partiallyAnswered: false,
    notAnswered: false
  });
  const [auditModal, setAuditModal] = useState({
    visible: false,
    questionId: null
  });

  useEffect(() => {
    loadDocumentAndQuestions();
  }, [documentId]);

  const triggerFlashAnimation = (tabs) => {
    // Flash the specified tabs
    setFlashingTabs(prev => ({
      ...prev,
      ...tabs
    }));
    
    // Clear the flash after animation duration
    setTimeout(() => {
      setFlashingTabs({
        answered: false,
        partiallyAnswered: false,
        notAnswered: false
      });
    }, 600); // 600ms for animation duration
  };

  const loadDocumentAndQuestions = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      // Load document details and questions in parallel
      const [documentResponse, questionsResponse] = await Promise.all([
        fetch(`http://localhost:8000/deals/${dealId}/documents`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`http://localhost:8000/documents/${documentId}/questions`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (!documentResponse.ok || !questionsResponse.ok) {
        throw new Error('Failed to load data');
      }

      const documentsData = await documentResponse.json();
      const questionsData = await questionsResponse.json();

      // Find the specific document
      const doc = documentsData.find(d => d.id === documentId);
      setDocument(doc);
      setQuestions(questionsData);
      
      // Separate questions by answer status
      const answered = questionsData.filter(q => q.answer_status === 'answered');
      const partiallyAnswered = questionsData.filter(q => q.answer_status === 'partiallyAnswered');
      const notAnswered = questionsData.filter(q => q.answer_status === 'notAnswered');
      setAnsweredQuestions(answered);
      setPartiallyAnsweredQuestions(partiallyAnswered);
      setNotAnsweredQuestions(notAnswered);
    } catch (error) {
      console.error('Error loading data:', error);
      setError('Failed to load document questions');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerEdit = (questionId, currentAnswer) => {
    setEditingAnswer(questionId);
    setAnswerText(currentAnswer || '');
  };

  const handleAnswerSave = async (questionId, addToKnowledgeBase = false) => {
    try {
      // Find the current question to check its previous state
      const currentQuestion = questions.find(q => q.id === questionId);
      const hadAnswer = currentQuestion?.answer_text && currentQuestion.answer_text.trim();
      const willHaveAnswer = answerText && answerText.trim();
      
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/questions/${questionId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          answer_text: answerText
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save answer');
      }

      // If user chose to add to knowledge base, do that now
      if (addToKnowledgeBase && answerText.trim()) {
        try {
          await handleAddToKnowledgeBase(questionId);
          toast.success('Answer saved and added to project knowledge base!');
        } catch (error) {
          // Answer was saved, but knowledge base addition failed
          toast.error('Answer saved, but failed to add to knowledge base: ' + error.message);
        }
      } else {
        toast.success('Answer saved successfully!');
      }

      // Save current scroll position
      const scrollPosition = window.pageYOffset || (document.documentElement && document.documentElement.scrollTop) || (document.body && document.body.scrollTop) || 0;
      
      // Reload the questions to get updated categories
      await loadDocumentAndQuestions();
      
      // Restore scroll position after re-render
      setTimeout(() => {
        window.scrollTo(0, scrollPosition);
      }, 0);
      
      // Trigger flash animation if answer status changed
      if (!hadAnswer && willHaveAnswer) {
        // Question went from unanswered to answered
        triggerFlashAnimation({
          answered: true,
          notAnswered: true
        });
      } else if (hadAnswer && !willHaveAnswer) {
        // Question went from answered to unanswered (answer removed)
        triggerFlashAnimation({
          answered: true,
          notAnswered: true
        });
      }
      
      setEditingAnswer(null);
      setAnswerText('');
    } catch (error) {
      console.error('Error saving answer:', error);
      toast.error('Failed to save answer. Please try again.');
    }
  };

  const handleAnswerCancel = () => {
    setEditingAnswer(null);
    setAnswerText('');
  };

  const handleCloseAuditModal = () => {
    setAuditModal({ visible: false, questionId: null });
  };

  const handleAddToKnowledgeBase = async (questionId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/questions/${questionId}/add-to-knowledge-base`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add to knowledge base');
      }

      const result = await response.json();
      console.log('Successfully added to knowledge base:', result);
    } catch (error) {
      console.error('Error adding to knowledge base:', error);
      throw error; // Re-throw so the calling function can handle the error
    }
  };


  const handleExport = async () => {
    try {
      setExportLoading(true);
      const token = localStorage.getItem('token');
      
      // Start export job for this specific document
      const response = await fetch(`${API_BASE_URL}/api/deals/${dealId}/documents/${documentId}/export`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to start export');
      }

      const exportData = await response.json();
      setExportStatus(exportData);
      
      // Poll for export completion
      pollExportStatus(exportData.id);
      
    } catch (error) {
      console.error('Error starting export:', error);
      toast.error(`Failed to start export: ${error.message}`);
      setExportLoading(false);
    }
  };

  const pollExportStatus = async (exportId) => {
    const token = localStorage.getItem('token');
    
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/exports/${exportId}/status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
          throw new Error('Failed to check export status');
        }

        const status = await response.json();
        setExportStatus(status);

        if (status.status === 'completed') {
          setExportLoading(false);
          // Auto-download the file
          downloadExportFile(exportId);
        } else if (status.status === 'failed') {
          setExportLoading(false);
          toast.error(`Export failed: ${status.error_message}`);
        } else if (status.status === 'processing' || status.status === 'pending') {
          // Continue polling
          setTimeout(checkStatus, 2000);
        }
      } catch (error) {
        console.error('Error checking export status:', error);
        setExportLoading(false);
        toast.error(`Error checking export status: ${error.message}`);
      }
    };

    checkStatus();
  };

  const downloadExportFile = async (exportId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/exports/${exportId}/download`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to download export file');
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `export-${exportId}.xlsx`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create blob and trigger download
      const blob = await response.blob();
      
      // Use the modern File System Access API if available, otherwise fallback
      if ('showSaveFilePicker' in window) {
        try {
          const fileHandle = await window.showSaveFilePicker({
            suggestedName: filename,
            types: [{
              description: 'Excel files',
              accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] }
            }]
          });
          const writable = await fileHandle.createWritable();
          await writable.write(blob);
          await writable.close();
          return;
        } catch (err) {
          // User cancelled or API not supported, fall back to blob URL
        }
      }
      
      // Fallback: use blob URL and anchor click
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      console.log('Export downloaded successfully');
    } catch (error) {
      console.error('Error downloading export:', error);
      toast.error(`Failed to download export: ${error.message}`);
    }
  };

  const handleDownloadDocument = async (documentId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        toast.error('Authentication required. Please log in again.');
        return;
      }

      console.log('Downloading document:', documentId);
      const response = await fetch(`${API_BASE_URL}/documents/${documentId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log('Download response status:', response.status);
      console.log('Download response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Download error response:', errorText);
        throw new Error(`Failed to download document: ${response.status} ${errorText}`);
      }

      // Get filename from Content-Disposition header or use a default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `document-${documentId}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      console.log('Download filename:', filename);

      // Create blob and download
      const blob = await response.blob();
      
      // Use a simpler approach with window.open and blob URL
      const url = URL.createObjectURL(blob);
      
      // Try to trigger download using a temporary anchor element
      try {
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = filename;
        anchor.style.display = 'none';
        
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
      } catch (domError) {
        console.warn('DOM approach failed, trying window.open:', domError);
        // Fallback: open in new window/tab
        window.open(url, '_blank');
      } finally {
        // Clean up the object URL after a short delay
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
      
      console.log('Download completed successfully');
    } catch (error) {
      console.error('Error downloading document:', error);
      toast.error(`Failed to download document: ${error.message}`);
    }
  };

  const getConfidenceBadge = (confidence) => {
    if (!confidence) return null;
    
    const percentage = Math.round(confidence * 100);
    let colorClass = 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    
    if (percentage >= 90) colorClass = 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300';
    else if (percentage >= 70) colorClass = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300';
    else if (percentage >= 50) colorClass = 'bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-300';
    else colorClass = 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300';

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
        {percentage}% confident
      </span>
    );
  };

  const getRelevanceBadge = (relevanceScore) => {
    if (!relevanceScore && relevanceScore !== 0) return null;
    
    const percentage = Math.round(relevanceScore);
    let colorClass = 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    
    if (percentage >= 90) colorClass = 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300';
    else if (percentage >= 70) colorClass = 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300';
    else if (percentage >= 50) colorClass = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300';
    else colorClass = 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300';

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
        {percentage}% relevant
      </span>
    );
  };

  const getProcessingStatusBadge = (status) => {
    const configs = {
      pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
      processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300',
      processed: 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300',
      error: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'
    };

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${configs[status] || configs.pending}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="text-gray-600 dark:text-gray-400">Loading questions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mb-4" />
        <div className="text-red-600 dark:text-red-400 text-center">
          <p className="text-lg font-medium">Error Loading Questions</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
        <button
          onClick={() => navigate(`/deals/${dealId}`)}
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Deal
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate(`/deals/${dealId}`)}
              className="inline-flex items-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <ArrowLeftIcon className="h-5 w-5 mr-2" />
              Back to Deal
            </button>
          </div>
          
          {/* Export Button */}
          <div className="flex items-center space-x-2">
            {exportStatus && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Export: <span className={`font-medium ${
                  exportStatus.status === 'completed' ? 'text-green-600 dark:text-green-400' :
                  exportStatus.status === 'failed' ? 'text-red-600 dark:text-red-400' :
                  'text-blue-600 dark:text-blue-400'
                }`}>
                  {exportStatus.status}
                </span>
                {exportStatus.status === 'completed' && (
                  <span className="ml-1">
                    ({exportStatus.answered_count}/{exportStatus.questions_count} answered)
                  </span>
                )}
              </div>
            )}
            <button
              onClick={handleExport}
              disabled={exportLoading || questions.length === 0}
              className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm ${
                exportLoading || questions.length === 0
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed dark:bg-gray-600 dark:text-gray-400'
                  : 'text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600'
              } transition-colors`}
            >
              {exportLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                  Export Deal
                </>
              )}
            </button>
          </div>
        </div>
        
        <div className="mt-4">
          <div className="flex items-center space-x-3">
            <DocumentTextIcon className="h-8 w-8 text-blue-500" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Questions from Document
              </h1>
              {document && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {document.original_filename} • {questions.length} question{questions.length !== 1 ? 's' : ''} extracted
                </p>
              )}
            </div>
          </div>

          {/* Tabs */}
          {questions.length > 0 && (
            <div className="mt-6">
              <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="-mb-px flex space-x-8">
                  <button
                    onClick={() => setActiveTab('answered')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'answered'
                        ? 'border-green-500 text-green-600 dark:text-green-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-5 w-5" />
                      <span>Answered Questions</span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-all duration-300 ${
                        activeTab === 'answered' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      } ${
                        flashingTabs.answered 
                          ? 'animate-pulse bg-green-400 text-white shadow-lg shadow-green-400/50 scale-110' 
                          : ''
                      }`}>
                        {answeredQuestions.length}
                      </span>
                    </div>
                  </button>
                  <button
                    onClick={() => setActiveTab('partiallyAnswered')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'partiallyAnswered'
                        ? 'border-yellow-500 text-yellow-600 dark:text-yellow-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <ExclamationTriangleIcon className="h-5 w-5" />
                      <span>Partially Answered Questions</span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-all duration-300 ${
                        activeTab === 'partiallyAnswered' 
                          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      } ${
                        flashingTabs.partiallyAnswered 
                          ? 'animate-pulse bg-yellow-400 text-white shadow-lg shadow-yellow-400/50 scale-110' 
                          : ''
                      }`}>
                        {partiallyAnsweredQuestions.length}
                      </span>
                    </div>
                  </button>
                  <button
                    onClick={() => setActiveTab('notAnswered')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'notAnswered'
                        ? 'border-red-500 text-red-600 dark:text-red-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <XCircleIcon className="h-5 w-5" />
                      <span>Not Answered Questions</span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-all duration-300 ${
                        activeTab === 'notAnswered' 
                          ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      } ${
                        flashingTabs.notAnswered 
                          ? 'animate-pulse bg-red-400 text-white shadow-lg shadow-red-400/50 scale-110' 
                          : ''
                      }`}>
                        {notAnsweredQuestions.length}
                      </span>
                    </div>
                  </button>
                </nav>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Questions Content */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        {questions.length === 0 ? (
          <div className="text-center py-8">
            <QuestionMarkCircleIcon className="mx-auto h-16 w-16 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">No Questions Found</h3>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              No questions were extracted from this document. This could mean:
            </p>
            <ul className="mt-4 text-sm text-gray-500 dark:text-gray-400 space-y-1">
              <li>• The document is still being processed</li>
              <li>• The document doesn't contain any questions</li>
              <li>• The extraction process encountered an error</li>
            </ul>
          </div>
        ) : (
          <>
            {(activeTab === 'answered' ? answeredQuestions : activeTab === 'partiallyAnswered' ? partiallyAnsweredQuestions : notAnsweredQuestions).length === 0 ? (
              <div className="text-center py-8">
                <QuestionMarkCircleIcon className="mx-auto h-16 w-16 text-gray-400" />
                <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                  No {activeTab} questions found
                </h3>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  {activeTab === 'answered' 
                    ? 'No questions have been successfully answered yet.'
                    : activeTab === 'partiallyAnswered'
                    ? 'No questions are currently partially answered.'
                    : 'No questions are currently not answered.'
                  }
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {(activeTab === 'answered' ? answeredQuestions : activeTab === 'partiallyAnswered' ? partiallyAnsweredQuestions : notAnsweredQuestions).map((question, index) => (
            <div key={question.id} className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white line-clamp-2">
                      {question.question_text}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Answer Status: <span className={`font-medium ${
                        activeTab === 'answered' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {question.answer_status}
                      </span>
                      {(question.last_edited_by || question.answer_status === 'answered') && (
                        <>
                          {' by '}
                          <span 
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              question.last_edit_source === 'ai_initial' 
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300'
                                : question.last_edit_source === 'user_edit' || question.last_edit_source === 'user_create'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                                : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                            }`}
                          >
                            {question.last_edit_source === 'ai_initial' ? 'ImogenRFP' : 
                             (question.last_edited_by === 'System' ? 'ImogenRFP' : question.last_edited_by) || 'ImogenRFP'}
                          </span>
                          <button
                            onClick={() => setAuditModal({ visible: true, questionId: question.id })}
                            className="ml-2 inline-flex items-center px-2 py-1 bg-gray-50 hover:bg-gray-100 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 border border-gray-200 dark:border-gray-600 rounded text-xs font-medium transition-colors"
                            title="View edit history"
                          >
                            <ClockIcon className="h-3 w-3 mr-1" />
                            History
                          </button>
                        </>
                      )}
                    </p>
                </div>
                <div className="flex items-center space-x-2">
                  {getProcessingStatusBadge(question.processing_status)}
                  {getConfidenceBadge(question.extraction_confidence)}
                  {getRelevanceBadge(question.answer_relevance_score)}
                </div>
              </div>



              {/* Answer Section */}
              <div className="space-y-3">
                {editingAnswer === question.id ? (
                  <div className="space-y-3">
                    <textarea
                      value={answerText}
                      onChange={(e) => setAnswerText(e.target.value)}
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="Enter your answer here..."
                    />
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => handleAnswerSave(question.id, false)}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                      >
                        <CheckIcon className="h-4 w-4 mr-2" />
                        Save Answer
                      </button>
                      <button
                        onClick={() => handleAnswerSave(question.id, true)}
                        disabled={!answerText.trim()}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <BookOpenIcon className="h-4 w-4 mr-2" />
                        Save & Add to Knowledge Base
                      </button>
                      <button
                        onClick={handleAnswerCancel}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div 
                      onClick={() => handleAnswerEdit(question.id, question.answer_text)}
                      className="min-h-20 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 cursor-text hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                    >
                      {question.answer_text ? (
                        <p className="text-gray-900 dark:text-white whitespace-pre-wrap">
                          {question.answer_text}
                        </p>
                      ) : (
                        <p className="text-gray-500 dark:text-gray-400 italic">
                          Click to add your answer...
                        </p>
                      )}
                    </div>
                    
                    {/* Always visible edit button */}
                    <button
                      onClick={() => handleAnswerEdit(question.id, question.answer_text)}
                      className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                    >
                      <PencilIcon className="h-4 w-4 mr-2" />
                      {question.answer_text ? 'Improve this answer' : 'Answer this question'}
                    </button>
                  </div>
                )}
              </div>

              {/* Sources Section */}
              {question.answer_sources && question.answer_sources.length > 0 && (
                <div className="mt-4 space-y-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Sources
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {question.answer_sources.map((sourceId, index) => {
                      const filename = question.answer_source_filenames && question.answer_source_filenames[index] 
                        ? question.answer_source_filenames[index] 
                        : `Document ${index + 1}`;
                      
                      return (
                        <button
                          key={index}
                          onClick={() => handleDownloadDocument(sourceId)}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-900/70 transition-colors cursor-pointer"
                          title={`Download ${filename}`}
                        >
                          <DocumentTextIcon className="h-3 w-3 mr-1" />
                          {filename}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Audit History Modal */}
      <AuditHistoryModal
        questionId={auditModal.questionId}
        isVisible={auditModal.visible}
        onClose={handleCloseAuditModal}
      />
    </div>
  );
};

export default DocumentQuestions;