#!/usr/bin/env python3
"""
Script to create the Elasticsearch index for Info Hunter.
Run this after starting Elasticsearch to initialize the search index.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.search.index import create_index, INDEX_NAME
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to create the Elasticsearch index."""
    logger.info(f"Creating Elasticsearch index: {INDEX_NAME}")
    
    if create_index():
        logger.info("Index created successfully!")
        return 0
    else:
        logger.error("Failed to create index")
        return 1


if __name__ == "__main__":
    sys.exit(main())

