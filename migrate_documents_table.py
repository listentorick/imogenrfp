#!/usr/bin/env python3
"""
Migration script to add deal_id and document_type columns to documents table
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def run_migration():
    # Database connection parameters
    db_params = {
        'host': 'localhost',
        'port': '5432',
        'database': 'rfp_saas',
        'user': 'rfp_user',
        'password': 'rfp_password'
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("Adding new columns to documents table...")
        
        # Add deal_id column
        try:
            cur.execute("""
                ALTER TABLE documents 
                ADD COLUMN deal_id UUID REFERENCES deals(id)
            """)
            print("✓ Added deal_id column")
        except psycopg2.errors.DuplicateColumn:
            print("✓ deal_id column already exists")
        
        # Add document_type column
        try:
            cur.execute("""
                ALTER TABLE documents 
                ADD COLUMN document_type VARCHAR(50) DEFAULT 'rfp'
            """)
            print("✓ Added document_type column")
        except psycopg2.errors.DuplicateColumn:
            print("✓ document_type column already exists")
        
        # Make project_id nullable
        try:
            cur.execute("""
                ALTER TABLE documents 
                ALTER COLUMN project_id DROP NOT NULL
            """)
            print("✓ Made project_id nullable")
        except Exception as e:
            print(f"⚠ project_id change skipped: {e}")
        
        # Set default document_type for existing records
        cur.execute("""
            UPDATE documents 
            SET document_type = 'other' 
            WHERE document_type IS NULL OR document_type = ''
        """)
        print("✓ Updated existing records with default document_type")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration()