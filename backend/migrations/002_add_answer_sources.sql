-- Add answer_sources column to questions table
-- This will store an array of document IDs that were used as sources for the answer

ALTER TABLE questions ADD COLUMN answer_sources TEXT[] DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN questions.answer_sources IS 'Array of document IDs that were used as sources for the answer from ChromaDB';