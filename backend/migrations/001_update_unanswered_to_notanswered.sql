-- Migration to update existing 'unanswered' status to 'notAnswered'
-- This migration standardizes the answer status terminology

BEGIN;

-- Update all 'unanswered' records to 'notAnswered'
UPDATE questions SET answer_status = 'notAnswered' WHERE answer_status = 'unanswered';

-- Drop and recreate the check constraint to allow only 'answered', 'notAnswered', 'partiallyAnswered'
ALTER TABLE questions DROP CONSTRAINT IF EXISTS check_answer_status;
ALTER TABLE questions ADD CONSTRAINT check_answer_status 
    CHECK (answer_status IN ('answered', 'notAnswered', 'partiallyAnswered'));

-- Update the column comment
COMMENT ON COLUMN questions.answer_status IS 'Status indicating if question was successfully answered: answered, notAnswered, partiallyAnswered';

COMMIT;