-- Add answer_source_filenames column to questions table
-- This will store an array of original filenames corresponding to the answer_sources

ALTER TABLE questions ADD COLUMN answer_source_filenames TEXT[] DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN questions.answer_source_filenames IS 'Array of original filenames corresponding to answer_sources document IDs';