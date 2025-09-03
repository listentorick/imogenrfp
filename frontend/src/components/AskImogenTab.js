import React, { useState, useCallback, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, ChatBubbleLeftRightIcon, UserIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline';
import { api } from '../utils/api';
import ReactMarkdown from 'react-markdown';

const AskImogenTab = ({ projectId }) => {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = useCallback(async (messageText = currentMessage) => {
    if (!messageText.trim() || isLoading) return;
    
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: messageText,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);
    
    // Create placeholder AI message for streaming
    const aiMessageId = Date.now() + 1;
    const aiMessage = {
      id: aiMessageId,
      type: 'ai',
      content: '',
      sources: [],
      source_documents: [],
      context_chunks_used: 0,
      debug_prompt: '',
      thinking: null,
      timestamp: new Date(),
      isStreaming: true,
      isThinking: false
    };
    
    setMessages(prev => {
      console.log('Adding AI message with ID:', aiMessageId);
      console.log('Current messages before adding:', prev.length);
      return [...prev, aiMessage];
    });
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/projects/${projectId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: messageText })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamedContent = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last potentially incomplete line in buffer
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6); // Remove 'data: '
              if (jsonStr.trim() === '') continue; // Skip empty data lines
              
              const data = JSON.parse(jsonStr);
              
              if (data.type === 'metadata') {
                // Store metadata but don't show sources yet - wait until streaming is complete
                console.log('Received metadata:', data);
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { 
                        ...msg, 
                        _pendingSources: data.sources || [],
                        _pendingSourceDocuments: data.source_documents || [],
                        _pendingContextChunksUsed: data.context_chunks_used || 0,
                        debug_prompt: data.debug_prompt || ''
                      }
                    : msg
                ));
              } else if (data.type === 'thinking_start') {
                // Show thinking indicator
                console.log('Thinking started');
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, isThinking: true }
                    : msg
                ));
              } else if (data.type === 'thinking_end') {
                // Hide thinking indicator and start showing content
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { 
                        ...msg, 
                        isThinking: false,
                        thinking: data.thinking || null
                      }
                    : msg
                ));
              } else if (data.type === 'token') {
                // Append token to content
                streamedContent += data.token;
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, content: streamedContent }
                    : msg
                ));
              } else if (data.type === 'complete') {
                // Final update with clean response and thinking - now show sources
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { 
                        ...msg, 
                        content: data.clean_response || streamedContent,
                        thinking: data.thinking,
                        isStreaming: false,
                        isThinking: false,
                        // Move pending metadata to visible fields
                        sources: msg._pendingSources || [],
                        source_documents: msg._pendingSourceDocuments || [],
                        context_chunks_used: msg._pendingContextChunksUsed || 0,
                        // Clean up pending fields
                        _pendingSources: undefined,
                        _pendingSourceDocuments: undefined,
                        _pendingContextChunksUsed: undefined
                      }
                    : msg
                ));
              } else if (data.type === 'error') {
                throw new Error(data.error);
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat failed:', error);
      const errorMessage = {
        id: Date.now() + 2,
        type: 'error',
        content: error.message || 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => prev.filter(msg => msg.id !== aiMessageId).concat([errorMessage]));
    } finally {
      setIsLoading(false);
    }
  }, [projectId, currentMessage, isLoading]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };


  return (
    <div className="flex flex-col h-[600px]">
      {/* Chat Messages */}
      <div className="flex-1 bg-white border border-gray-200 rounded-lg mb-4 overflow-hidden">
        <div className="h-full flex flex-col">
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <div className="bg-blue-50 rounded-full p-3 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                  <ChatBubbleLeftRightIcon className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Chat with Imogen</h3>
                <p className="text-gray-600 mb-6">Ask questions about your knowledge base documents</p>
                
                {/* Suggestion Chips */}
                <div className="flex flex-wrap justify-center gap-2">
                  {[
                    "What are the key requirements?",
                    "Show me pricing information",
                    "Find technical specifications",
                    "What are the deadlines?"
                  ].map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="text-sm bg-blue-50 border border-blue-200 rounded-full px-4 py-2 hover:bg-blue-100 text-blue-700 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex items-start space-x-3 max-w-[80%] ${
                    message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}>
                    {/* Avatar */}
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      message.type === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : message.type === 'error'
                        ? 'bg-red-100 text-red-600'
                        : 'bg-purple-100 text-purple-600'
                    }`}>
                      {message.type === 'user' ? (
                        <UserIcon className="h-4 w-4" />
                      ) : (
                        <ComputerDesktopIcon className="h-4 w-4" />
                      )}
                    </div>
                    
                    {/* Message Content */}
                    <div className={`rounded-lg px-4 py-3 ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.type === 'error'
                        ? 'bg-red-50 border border-red-200 text-red-800'
                        : 'bg-gray-100 text-gray-900'
                    }`}>
                      {message.isThinking ? (
                        <div className="flex items-center space-x-2">
                          <div className="animate-pulse flex space-x-1">
                            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                          </div>
                          <span className="text-sm text-purple-600">Imogen is thinking...</span>
                        </div>
                      ) : (
                        <div className="text-sm prose prose-sm max-w-none">
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                          {message.isStreaming && !message.isThinking && (
                            <span className="inline-block w-2 h-4 bg-gray-600 ml-1 animate-pulse">|</span>
                          )}
                        </div>
                      )}
                      
                      {/* Sources and Debug Info for AI messages - only show when not streaming */}
                      {message.type === 'ai' && !message.isStreaming && (
                        <div className="mt-3 pt-3 border-t border-gray-200 space-y-3">
                          {(message.source_documents?.length > 0 || message.sources?.length > 0) && (
                            <div>
                              <p className="text-xs text-gray-600 mb-2">Sources ({message.context_chunks_used} chunks):</p>
                              <div className="flex flex-wrap gap-1">
                                {message.source_documents?.map((doc, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => {
                                      const token = localStorage.getItem('token');
                                      const link = document.createElement('a');
                                      link.href = `http://localhost:8000/documents/${doc.id}/download?token=${encodeURIComponent(token)}`;
                                      link.download = doc.filename;
                                      link.target = '_blank';
                                      document.body.appendChild(link);
                                      link.click();
                                      document.body.removeChild(link);
                                    }}
                                    className="text-xs bg-white border border-gray-300 rounded px-2 py-1 text-blue-700 hover:bg-blue-50 hover:border-blue-400 transition-colors cursor-pointer"
                                    title={`Download ${doc.filename}`}
                                  >
                                    {doc.filename}
                                  </button>
                                )) || message.sources?.map((source, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => window.open(`/projects/${projectId}/knowledge`, '_blank')}
                                    className="text-xs bg-white border border-gray-300 rounded px-2 py-1 text-blue-700 hover:bg-blue-50 hover:border-blue-400 transition-colors cursor-pointer"
                                    title={`View ${source} in Knowledge Base`}
                                  >
                                    {source}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Debug Info */}
                          {(message.debug_prompt || message.thinking) && (
                            <div className="text-xs space-y-2">
                              {message.thinking && (
                                <details>
                                  <summary className="text-gray-600 cursor-pointer hover:text-gray-800">Debug: LLM Thinking</summary>
                                  <pre className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-gray-700 whitespace-pre-wrap font-mono text-xs overflow-x-auto">
                                    {message.thinking}
                                  </pre>
                                </details>
                              )}
                              
                              {message.debug_prompt && (
                                <details>
                                  <summary className="text-gray-600 cursor-pointer hover:text-gray-800">Debug: Full LLM Prompt</summary>
                                  <pre className="mt-2 p-2 bg-gray-50 border border-gray-200 rounded text-gray-700 whitespace-pre-wrap font-mono text-xs overflow-x-auto">
                                    {message.debug_prompt}
                                  </pre>
                                </details>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                      
                      <div className="text-xs mt-2 opacity-70">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
            
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask Imogen about your documents..."
                  rows={1}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                />
              </div>
              <button
                onClick={() => sendMessage()}
                disabled={!currentMessage.trim() || isLoading}
                className="bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>


    </div>
  );
};

export default AskImogenTab;