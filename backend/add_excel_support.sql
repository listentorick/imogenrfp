-- Add Excel support to questions table
ALTER TABLE questions ADD COLUMN answer_cell_reference VARCHAR(10);
ALTER TABLE questions ADD COLUMN cell_confidence NUMERIC(3, 2);
ALTER TABLE questions ADD COLUMN sheet_name VARCHAR(255);
ALTER TABLE questions ADD COLUMN document_type VARCHAR(50);

-- Create indexes for performance
CREATE INDEX idx_questions_document_type ON questions(document_type);
CREATE INDEX idx_questions_answer_cell ON questions(answer_cell_reference);