-- Add answer status field to questions table
DO $$ 
BEGIN
    -- Add answer_status column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'questions' AND column_name = 'answer_status') THEN
        ALTER TABLE questions ADD COLUMN answer_status VARCHAR(50) DEFAULT 'unanswered' NOT NULL;
    END IF;
END $$;

-- Add check constraint for valid answer statuses (ignore if already exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage 
                   WHERE constraint_name = 'check_answer_status') THEN
        ALTER TABLE questions ADD CONSTRAINT check_answer_status 
            CHECK (answer_status IN ('answered', 'unanswered'));
    END IF;
END $$;

-- Add index for performance when filtering by answer status
CREATE INDEX IF NOT EXISTS idx_questions_answer_status ON questions(answer_status);

-- Update existing questions to have unanswered status by default
UPDATE questions SET answer_status = 'unanswered' WHERE answer_status IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN questions.answer_status IS 'Status indicating if question was successfully answered: answered, unanswered';