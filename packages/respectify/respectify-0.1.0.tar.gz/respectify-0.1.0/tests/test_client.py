"""Tests for the synchronous Respectify client."""

import os
import uuid
import pytest
from uuid import UUID
from typing import List
from dotenv import load_dotenv

from respectify import (
    RespectifyClient,
    CommentScore,
    DogwhistleResult,
    MegaCallResult,
    SpamDetectionResult,
    CommentRelevanceResult,
    InitTopicResponse,
    UserCheckResponse,
    AuthenticationError,
    BadRequestError,
)


# Load environment variables for testing
load_dotenv()


class TestRespectifyClient:
    """Test cases for the synchronous Respectify client."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with credentials and client."""
        cls.email = os.getenv('RESPECTIFY_EMAIL')
        cls.api_key = os.getenv('RESPECTIFY_API_KEY')
        cls.base_url = os.getenv('RESPECTIFY_BASE_URL')
        cls.test_article_id = UUID(os.getenv('REAL_ARTICLE_ID', str(uuid.uuid4())))
        
        if not cls.email or not cls.api_key:
            pytest.skip("Missing RESPECTIFY_EMAIL or RESPECTIFY_API_KEY environment variables")
        
        cls.client = RespectifyClient(
            email=cls.email,
            api_key=cls.api_key,
            base_url=cls.base_url
        )
        
        print(f"\nUsing real API with email: {cls.email} at {cls.base_url or 'https://app.respectify.org (default)'}")
    
    def test_init_topic_from_text_success(self):
        """Test successful topic initialization from text."""
        result = self.client.init_topic_from_text('Sample text for testing')
        
        assert isinstance(result, InitTopicResponse)
        assert isinstance(result.article_id, UUID)
    
    def test_init_topic_from_text_bad_request(self):
        """Test topic initialization with empty text raises BadRequestError."""
        with pytest.raises(BadRequestError):
            self.client.init_topic_from_text('')
    
    def test_init_topic_from_url_success(self):
        """Test successful topic initialization from URL."""
        result = self.client.init_topic_from_url(
            'https://daveon.design/creating-joy-in-the-user-experience.html'
        )
        
        assert isinstance(result, InitTopicResponse)
        assert isinstance(result.article_id, UUID)
    
    def test_init_topic_from_url_bad_request(self):
        """Test topic initialization with empty URL raises BadRequestError."""
        with pytest.raises(BadRequestError):
            self.client.init_topic_from_url('')
    
    def test_evaluate_comment_success(self):
        """Test successful comment evaluation."""
        result = self.client.evaluate_comment(
            'This is a test comment',
            self.test_article_id
        )
        
        assert isinstance(result, CommentScore)
        assert result.overall_score <= 2  # Real-world result will be 1 or 2
        assert isinstance(result.toxicity_score, float)
        assert 0.0 <= result.toxicity_score <= 1.0
        assert isinstance(result.toxicity_explanation, str)
    
    def test_evaluate_comment_bad_request(self):
        """Test comment evaluation with empty comment raises BadRequestError."""
        with pytest.raises(BadRequestError):
            self.client.evaluate_comment('', self.test_article_id)
    
    def test_evaluate_comment_unauthorized(self):
        """Test comment evaluation with wrong credentials raises AuthenticationError."""
        wrong_client = RespectifyClient('wrong-email@example.com', 'wrong-api-key')
        
        with pytest.raises(AuthenticationError):
            wrong_client.evaluate_comment('This is a test comment', self.test_article_id)
    
    def test_check_user_credentials_success(self):
        """Test successful user credentials check."""
        result = self.client.check_user_credentials()
        
        assert isinstance(result, UserCheckResponse)
        assert result.success is True
        assert result.message == ''
    
    def test_check_user_credentials_unauthorized(self):
        """Test user credentials check with wrong credentials."""
        wrong_client = RespectifyClient('wrong-email@example.com', 'wrong-api-key')
        result = wrong_client.check_user_credentials()
        
        assert isinstance(result, UserCheckResponse)
        assert result.success is False
        assert 'Unauthorized' in result.message
        assert 'email' in result.message
        assert 'API key' in result.message
    
    def test_check_spam_success(self):
        """Test successful spam detection."""
        result = self.client.check_spam(
            'This is a test comment that might be spam',
            self.test_article_id
        )
        
        assert isinstance(result, SpamDetectionResult)
        assert isinstance(result.is_spam, bool)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0
    
    def test_check_spam_without_article_context_success(self):
        """Test successful spam detection without article context."""
        # Create article ID from UUID for the test
        test_uuid = uuid.uuid4()
        result = self.client.check_spam(
            'This is a comment without specific article context',
            test_uuid
        )
        
        assert isinstance(result, SpamDetectionResult)
        assert isinstance(result.is_spam, bool)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
    
    def test_check_spam_bad_request(self):
        """Test spam detection with empty comment raises BadRequestError."""
        with pytest.raises(BadRequestError):
            self.client.check_spam('', self.test_article_id)
    
    def test_check_relevance_success(self):
        """Test successful relevance check."""
        result = self.client.check_relevance(
            'This is a relevant comment',
            self.test_article_id
        )
        
        assert isinstance(result, CommentRelevanceResult)
        
        # Check OnTopicResult
        assert isinstance(result.on_topic.is_on_topic, bool)
        assert isinstance(result.on_topic.confidence, float)
        assert 0.0 <= result.on_topic.confidence <= 1.0
        assert isinstance(result.on_topic.reasoning, str)
        
        # Check BannedTopicsResult
        assert isinstance(result.banned_topics.banned_topics, list)
        assert isinstance(result.banned_topics.quantity_on_banned_topics, float)
        assert 0.0 <= result.banned_topics.quantity_on_banned_topics <= 1.0
    
    def test_check_relevance_with_banned_topics_success(self):
        """Test successful relevance check with banned topics."""
        result = self.client.check_relevance(
            'This comment discusses politics and religion',
            self.test_article_id,
            banned_topics=['politics', 'religion']
        )
        
        assert isinstance(result, CommentRelevanceResult)
        assert isinstance(result.banned_topics.banned_topics, list)
        assert len(result.banned_topics.banned_topics) > 0
        assert result.banned_topics.quantity_on_banned_topics > 0.0
        
        print(f"\nBanned topics test returned: banned_topics={result.banned_topics.banned_topics}, "
              f"quantity={result.banned_topics.quantity_on_banned_topics:.2f}")
    
    def test_check_relevance_bad_request(self):
        """Test relevance check with empty comment raises BadRequestError."""
        with pytest.raises(BadRequestError):
            self.client.check_relevance('', self.test_article_id)
    
    def test_check_dogwhistle_success(self):
        """Test successful dogwhistle detection."""
        result = self.client.check_dogwhistle(
            'This is a regular comment with no problematic content.'
        )
        
        assert isinstance(result, DogwhistleResult)
        assert isinstance(result.detection.reasoning, str)
        assert isinstance(result.detection.dogwhistles_detected, bool)
        assert isinstance(result.detection.confidence, float)
        assert 0.0 <= result.detection.confidence <= 1.0
        
        # Details can be None if no dogwhistles detected
        if result.details is not None:
            assert isinstance(result.details.dogwhistle_terms, list)
            assert isinstance(result.details.categories, list)
            assert isinstance(result.details.subtlety_level, float)
            assert 0.0 <= result.details.subtlety_level <= 1.0
            assert isinstance(result.details.harm_potential, float)
            assert 0.0 <= result.details.harm_potential <= 1.0
        
        print(f"\nDogwhistle check result: detected={result.detection.dogwhistles_detected}, "
              f"confidence={result.detection.confidence:.2f}")
    
    def test_check_dogwhistle_with_sensitive_topics_success(self):
        """Test successful dogwhistle detection with sensitive topics."""
        result = self.client.check_dogwhistle(
            'This is a comment to test with specific topics.',
            sensitive_topics=['politics', 'social issues']
        )
        
        assert isinstance(result, DogwhistleResult)
        assert isinstance(result.detection.reasoning, str)
        assert isinstance(result.detection.dogwhistles_detected, bool)
        assert isinstance(result.detection.confidence, float)
        
        print(f"\nDogwhistle check with sensitive topics: detected={result.detection.dogwhistles_detected}")
    
    def test_megacall_spam_only_success(self):
        """Test successful megacall with spam detection only."""
        result = self.client.megacall(
            'This is a test comment for spam check',
            self.test_article_id,
            include_spam=True
        )
        
        assert isinstance(result, MegaCallResult)
        assert isinstance(result.spam, SpamDetectionResult)
        assert isinstance(result.spam.is_spam, bool)
        assert isinstance(result.spam.confidence, float)
        assert 0.0 <= result.spam.confidence <= 1.0
        
        # Other services should be None
        assert result.relevance is None
        assert result.comment_score is None
        assert result.dogwhistle is None
        
        print(f"\nMegacall spam only: confidence={result.spam.confidence:.2f}")
    
    def test_megacall_relevance_only_success(self):
        """Test successful megacall with relevance check only."""
        result = self.client.megacall(
            'Beartype is a great type checker for Python',
            self.test_article_id,
            include_relevance=True
        )
        
        assert isinstance(result, MegaCallResult)
        assert isinstance(result.relevance, CommentRelevanceResult)
        assert isinstance(result.relevance.on_topic.is_on_topic, bool)
        assert isinstance(result.relevance.on_topic.confidence, float)
        
        # Other services should be None
        assert result.spam is None
        assert result.comment_score is None
        assert result.dogwhistle is None
    
    def test_megacall_comment_score_only_success(self):
        """Test successful megacall with comment scoring only."""
        result = self.client.megacall(
            'This is a test comment for comment score check',
            self.test_article_id,
            include_comment_score=True
        )
        
        assert isinstance(result, MegaCallResult)
        assert isinstance(result.comment_score, CommentScore)
        assert isinstance(result.comment_score.logical_fallacies, list)
        assert isinstance(result.comment_score.objectionable_phrases, list)
        assert isinstance(result.comment_score.negative_tone_phrases, list)
        assert isinstance(result.comment_score.appears_low_effort, bool)
        assert isinstance(result.comment_score.overall_score, int)
        assert 1 <= result.comment_score.overall_score <= 5
        assert isinstance(result.comment_score.toxicity_score, float)
        assert 0.0 <= result.comment_score.toxicity_score <= 1.0
        
        # Other services should be None
        assert result.spam is None
        assert result.relevance is None
        assert result.dogwhistle is None
    
    def test_megacall_all_services_success(self):
        """Test successful megacall with all services."""
        result = self.client.megacall(
            'Beartype is great for comprehensive analysis.',
            self.test_article_id,
            include_spam=True,
            include_relevance=True,
            include_comment_score=True,
            include_dogwhistle=True
        )
        
        assert isinstance(result, MegaCallResult)
        
        # All services should be present
        assert isinstance(result.spam, SpamDetectionResult)
        assert isinstance(result.relevance, CommentRelevanceResult)
        assert isinstance(result.comment_score, CommentScore)
        assert isinstance(result.dogwhistle, DogwhistleResult)
        
        # Basic validation for each service
        assert isinstance(result.spam.is_spam, bool)
        assert isinstance(result.relevance.on_topic.is_on_topic, bool)
        assert isinstance(result.comment_score.overall_score, int)
        assert isinstance(result.comment_score.toxicity_score, float)
        assert isinstance(result.dogwhistle.detection.dogwhistles_detected, bool)
        
        print(f"\nMegacall all services: spam={result.spam.confidence:.2f}, "
              f"relevance={result.relevance.on_topic.confidence:.2f}, "
              f"score={result.comment_score.overall_score}/5, "
              f"toxicity={result.comment_score.toxicity_score:.2f}, "
              f"dogwhistle={result.dogwhistle.detection.confidence:.2f}")
    
    def test_megacall_with_parameters_success(self):
        """Test successful megacall with additional parameters."""
        result = self.client.megacall(
            'This is a comprehensive test comment.',
            self.test_article_id,
            include_spam=True,
            include_relevance=True,
            include_comment_score=True,
            include_dogwhistle=True,
            banned_topics=['politics', 'religion'],
            sensitive_topics=['test topic'],
            dogwhistle_examples=['example phrase']
        )
        
        assert isinstance(result, MegaCallResult)
        assert all([
            result.spam is not None,
            result.relevance is not None,
            result.comment_score is not None,
            result.dogwhistle is not None
        ])
        
        print("\nMegacall with all parameters succeeded")