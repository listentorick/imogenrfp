import React from 'react';
import { useParams } from 'react-router-dom';
import AskImogenTab from '../components/AskImogenTab';

const AskImogen = () => {
  const { projectId } = useParams();

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Ask Imogen
        </h1>
        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Search through your knowledge base using AI-powered semantic search
        </div>
      </div>

      {/* Ask Imogen Component */}
      <AskImogenTab projectId={projectId} />
    </div>
  );
};

export default AskImogen;