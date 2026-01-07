"""
Stack Exchange connector for ingesting Q&A content.
Uses Stack Exchange API to fetch questions and answers by tags.
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
import logging
from app.ingest.base import BaseConnector
from app.config import settings
from app.utils.http_client import fetch_url

logger = logging.getLogger(__name__)


class StackExchangeConnector(BaseConnector):
    """
    Connector for ingesting Stack Overflow and Stack Exchange content.
    """
    
    def __init__(self, site: str = "stackoverflow"):
        """
        Initialize Stack Exchange connector.
        
        Args:
            site: Stack Exchange site identifier (default: stackoverflow)
        """
        super().__init__("Stack Overflow", "stackexchange")
        self.site = site
        self.api_base = "https://api.stackexchange.com/2.3"
        self.api_key = settings.stackexchange_key  # Optional but recommended
    
    def fetch_items(self, tags: Optional[List[str]] = None, max_items: int = 50, 
                   **kwargs) -> List[Dict]:
        """
        Fetch questions and answers from Stack Exchange.
        
        Args:
            tags: List of tags to filter by (e.g., ['python', 'javascript'])
            max_items: Maximum number of questions to fetch
            
        Returns:
            List of raw item dictionaries
        """
        items = []
        
        if not tags:
            tags = ['python', 'javascript', 'react', 'nodejs']  # Default tags
        
        try:
            # Fetch questions
            questions_url = f"{self.api_base}/questions"
            params = {
                "order": "desc",
                "sort": "activity",
                "tagged": ";".join(tags[:5]),  # API allows up to 5 tags
                "site": self.site,
                "pagesize": min(max_items, 100),  # API limit is 100
                "filter": "withbody",  # Include question body
            }
            
            if self.api_key:
                params["key"] = self.api_key
            
            logger.info(f"Fetching Stack Exchange questions with tags: {tags}")
            response = fetch_url(questions_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            questions = data.get('items', [])
            logger.info(f"Found {len(questions)} questions")
            
            # Process each question
            for question in questions:
                try:
                    item = self._process_question(question)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.warning(f"Error processing question {question.get('question_id')}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(items)} items")
            return items
            
        except Exception as e:
            logger.error(f"Error fetching Stack Exchange items: {e}", exc_info=True)
            return items
    
    def _process_question(self, question: Dict) -> Optional[Dict]:
        """
        Process a question into a raw item dictionary.
        
        Args:
            question: Question dictionary from Stack Exchange API
            
        Returns:
            Raw item dictionary or None if processing fails
        """
        question_id = question['question_id']
        question_url = question.get('link', f"https://{self.site}.com/questions/{question_id}")
        
        # Get accepted answer or top answer
        answer = None
        if question.get('accepted_answer_id'):
            answer = self._fetch_answer(question['accepted_answer_id'])
        elif question.get('answer_count', 0) > 0:
            # Fetch top answer
            answers_url = f"{self.api_base}/questions/{question_id}/answers"
            params = {
                "order": "desc",
                "sort": "votes",
                "site": self.site,
                "pagesize": 1,
                "filter": "withbody",
            }
            if self.api_key:
                params["key"] = self.api_key
            
            try:
                response = fetch_url(answers_url, timeout=30)
                response.raise_for_status()
                answers_data = response.json()
                if answers_data.get('items'):
                    answer = answers_data['items'][0]
            except Exception as e:
                logger.warning(f"Error fetching answer for question {question_id}: {e}")
        
        # Combine question and answer body
        body_html = question.get('body', '')
        if answer:
            body_html += "\n\n" + answer.get('body', '')
        
        # Extract tags
        tags = question.get('tags', [])
        
        # Detect primary language from tags
        primary_language = None
        language_tags = ['python', 'javascript', 'java', 'c', 'cpp', 'csharp', 'go', 
                        'rust', 'php', 'ruby', 'swift', 'kotlin', 'typescript']
        for tag in tags:
            if tag in language_tags:
                primary_language = tag.capitalize()
                break
        
        # Build item
        item = {
            'title': question.get('title', 'Untitled Question'),
            'content': body_html,
            'content_type': 'html',
            'source_url': question_url,
            'tags': tags,
            'primary_language': primary_language,
            'author': question.get('owner', {}).get('display_name') if question.get('owner') else None,
            'published_at': datetime.fromtimestamp(question.get('creation_date', 0)) if question.get('creation_date') else None,
            'summary': question.get('title'),
            # Additional metadata
            'stackexchange_score': question.get('score', 0),
            'stackexchange_answer_count': question.get('answer_count', 0),
            'stackexchange_view_count': question.get('view_count', 0),
        }
        
        return item
    
    def _fetch_answer(self, answer_id: int) -> Optional[Dict]:
        """
        Fetch a specific answer by ID.
        
        Args:
            answer_id: Answer ID
            
        Returns:
            Answer dictionary or None if not found
        """
        answer_url = f"{self.api_base}/answers/{answer_id}"
        params = {
            "site": self.site,
            "filter": "withbody",
        }
        
        if self.api_key:
            params["key"] = self.api_key
        
        try:
            response = fetch_url(answer_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('items'):
                return data['items'][0]
        except Exception as e:
            logger.warning(f"Error fetching answer {answer_id}: {e}")
        
        return None

