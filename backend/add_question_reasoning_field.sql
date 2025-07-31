-- Add reasoning field to questions table
DO $$ 
BEGIN
    -- Add reasoning column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'questions' AND column_name = 'reasoning') THEN
        ALTER TABLE questions ADD COLUMN reasoning TEXT;
    END IF;
END $$;

-- Add comments for documentation
COMMENT ON COLUMN questions.reasoning IS 'LLM reasoning extracted from <think> tags during question processing';