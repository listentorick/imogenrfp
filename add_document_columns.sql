-- Add new columns to documents table for deal support
-- This migration safely adds the new columns needed for deal documents

-- Add deal_id column (nullable, for deal documents only)
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS deal_id UUID REFERENCES deals(id);

-- Add document_type column with default value
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS document_type VARCHAR(50) DEFAULT 'other';

-- Update existing records to have a document_type
UPDATE documents 
SET document_type = 'other' 
WHERE document_type IS NULL OR document_type = '';

-- Add comment for clarity
COMMENT ON COLUMN documents.deal_id IS 'Foreign key to deals table - only set for deal documents, NULL for project documents';
COMMENT ON COLUMN documents.document_type IS 'Type of document: rfp, rfi, proposal, contract, other';