-- Add processing status fields to questions table
DO $$ 
BEGIN
    -- Add processing_status column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'questions' AND column_name = 'processing_status') THEN
        ALTER TABLE questions ADD COLUMN processing_status VARCHAR(50) DEFAULT 'pending' NOT NULL;
    END IF;
    
    -- Add processing_error column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'questions' AND column_name = 'processing_error') THEN
        ALTER TABLE questions ADD COLUMN processing_error TEXT;
    END IF;
END $$;

-- Add check constraint for valid processing statuses (ignore if already exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage 
                   WHERE constraint_name = 'check_processing_status') THEN
        ALTER TABLE questions ADD CONSTRAINT check_processing_status 
            CHECK (processing_status IN ('pending', 'processing', 'processed', 'error'));
    END IF;
END $$;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_questions_processing_status ON questions(processing_status);

-- Update existing questions to have pending status
UPDATE questions SET processing_status = 'pending' WHERE processing_status IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN questions.processing_status IS 'Status of question processing: pending, processing, processed, error';
COMMENT ON COLUMN questions.processing_error IS 'Error message if question processing fails';