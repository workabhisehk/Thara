#!/usr/bin/env python3
"""
Generate migration SQL from models without database connection.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import Base
from database.models import *  # noqa: F401, F403
from sqlalchemy.schema import CreateTable

def generate_create_statements():
    """Generate CREATE TABLE statements from models."""
    print("Generating SQL CREATE statements from models...")
    print("=" * 80)
    
    for table_name, table in Base.metadata.tables.items():
        print(f"\n-- Table: {table_name}")
        print(CreateTable(table).compile(compile_kwargs={"literal_binds": True}))
        print()
    
    # Print indexes separately
    print("\n-- Indexes:")
    for table_name, table in Base.metadata.tables.items():
        for index in table.indexes:
            print(f"-- Index on {table_name}: {index.name}")

if __name__ == "__main__":
    generate_create_statements()

