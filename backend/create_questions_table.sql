-- Create questions table for storing extracted questions from deal documents
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    answer_text TEXT,
    extraction_confidence NUMERIC(3,2) CHECK (extraction_confidence >= 0.00 AND extraction_confidence <= 1.00),
    question_order INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_questions_tenant_id ON questions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_questions_deal_id ON questions(deal_id);
CREATE INDEX IF NOT EXISTS idx_questions_document_id ON questions(document_id);
CREATE INDEX IF NOT EXISTS idx_questions_order ON questions(document_id, question_order);

-- Add comments for documentation
COMMENT ON TABLE questions IS 'Questions extracted from deal documents using LLM processing';
COMMENT ON COLUMN questions.tenant_id IS 'Reference to the tenant who owns this question';
COMMENT ON COLUMN questions.deal_id IS 'Reference to the deal this question belongs to';
COMMENT ON COLUMN questions.document_id IS 'Reference to the document this question was extracted from';
COMMENT ON COLUMN questions.question_text IS 'The actual question text extracted from the document';
COMMENT ON COLUMN questions.answer_text IS 'The answer to the question (filled manually or via LLM)';
COMMENT ON COLUMN questions.extraction_confidence IS 'Confidence score (0.00-1.00) from LLM extraction';
COMMENT ON COLUMN questions.question_order IS 'Sequential order of this question within the document';