import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon,
  QuestionMarkCircleIcon,
  DocumentTextIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

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

  useEffect(() => {
    loadDocumentAndQuestions();
  }, [documentId]);

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

  const handleAnswerSave = async (questionId) => {
    try {
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

      // Reload the questions to get updated categories
      await loadDocumentAndQuestions();
      
      setEditingAnswer(null);
      setAnswerText('');
    } catch (error) {
      console.error('Error saving answer:', error);
      alert('Failed to save answer. Please try again.');
    }
  };

  const handleAnswerCancel = () => {
    setEditingAnswer(null);
    setAnswerText('');
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
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        activeTab === 'answered' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
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
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        activeTab === 'partiallyAnswered' 
                          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
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
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        activeTab === 'notAnswered' 
                          ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
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
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      activeTab === 'answered' 
                        ? 'bg-green-100 dark:bg-green-900/50' 
                        : 'bg-red-100 dark:bg-red-900/50'
                    }`}>
                      {activeTab === 'answered' ? (
                        <CheckCircleIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
                      ) : (
                        <XCircleIcon className="h-5 w-5 text-red-600 dark:text-red-400" />
                      )}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Question {index + 1}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Answer Status: <span className={`font-medium ${
                        activeTab === 'answered' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {question.answer_status}
                      </span>
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {getProcessingStatusBadge(question.processing_status)}
                  {getConfidenceBadge(question.extraction_confidence)}
                  {getRelevanceBadge(question.answer_relevance_score)}
                </div>
              </div>

              {/* Question Text */}
              <div className="mb-6">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <p className="text-gray-900 dark:text-white font-medium">
                    {question.question_text}
                  </p>
                </div>
              </div>

              {/* Answer Section */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Answer
                </label>
                
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
                        onClick={() => handleAnswerSave(question.id)}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                      >
                        <CheckIcon className="h-4 w-4 mr-2" />
                        Save Answer
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
                )}
              </div>

              {/* Sources Section */}
              {question.answer_sources && question.answer_sources.length > 0 && (
                <div className="mt-4 space-y-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Sources
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {question.answer_sources.map((sourceId, index) => (
                      <button
                        key={index}
                        onClick={() => navigate(`/deals/${dealId}/documents/${sourceId}/questions`)}
                        className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-900/70 transition-colors"
                      >
                        <DocumentTextIcon className="h-3 w-3 mr-1" />
                        Document {index + 1}
                      </button>
                    ))}
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
    </div>
  );
};

export default DocumentQuestions;