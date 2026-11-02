"""Flag capture service for tracking exploits."""

import re
import uuid
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from services.common.config import settings
from services.common.logging import get_logger
from services.common.flags.models import Flag, FlagCapture, ALL_FLAGS, FlagCategory

logger = get_logger("flags")


class FlagService:
    """Service for managing flag captures and scoring."""
    
    # Regex to detect flags in responses
    FLAG_PATTERN = re.compile(r"FLAG\{[A-Za-z0-9_]+\}")
    
    def __init__(self):
        self._dynamodb: Optional[boto3.resource] = None
        self._local_captures: dict[str, list[FlagCapture]] = {}  # For local dev
    
    @property
    def dynamodb(self) -> boto3.resource:
        """Lazy-load DynamoDB resource."""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource(
                "dynamodb",
                region_name=settings.aws_region,
            )
        return self._dynamodb
    
    def capture(
        self,
        flag_id: str,
        user_id: str,
        method: str,
        payload: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[FlagCapture]:
        """
        Record a flag capture.
        
        Args:
            flag_id: ID of the captured flag
            user_id: User who captured the flag
            method: Method used to capture
            payload: Payload that triggered the capture
            ip_address: User's IP address
            user_agent: User's user agent
            
        Returns:
            FlagCapture record or None if invalid
        """
        flag = ALL_FLAGS.get(flag_id)
        if not flag:
            logger.warning("Invalid flag capture attempt", flag_id=flag_id)
            return None
        
        capture = FlagCapture(
            capture_id=str(uuid.uuid4()),
            user_id=user_id,
            flag_id=flag_id,
            timestamp=datetime.utcnow(),
            method=method,
            payload=payload[:1000],  # Limit payload size
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Store capture
        self._store_capture(capture)
        
        logger.info(
            "Flag captured!",
            flag_id=flag_id,
            user_id=user_id,
            method=method,
            points=flag.points,
        )
        
        return capture
    
    def _store_capture(self, capture: FlagCapture) -> None:
        """Store capture in DynamoDB or local storage."""
        if settings.environment.value == "local":
            # Local development - use in-memory storage
            if capture.user_id not in self._local_captures:
                self._local_captures[capture.user_id] = []
            self._local_captures[capture.user_id].append(capture)
            return
        
        try:
            table = self.dynamodb.Table(settings.dynamodb_table_scores)
            table.put_item(Item=capture.to_dict())
        except ClientError as e:
            logger.error("Failed to store capture", error=str(e))
    
    def get_user_captures(self, user_id: str) -> list[FlagCapture]:
        """Get all captures for a user."""
        if settings.environment.value == "local":
            return self._local_captures.get(user_id, [])
        
        try:
            table = self.dynamodb.Table(settings.dynamodb_table_scores)
            response = table.query(
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": user_id},
            )
            return [
                FlagCapture(**item) for item in response.get("Items", [])
            ]
        except ClientError as e:
            logger.error("Failed to get captures", error=str(e))
            return []
    
    def get_user_score(self, user_id: str) -> int:
        """Calculate total score for a user."""
        captures = self.get_user_captures(user_id)
        captured_flags = {c.flag_id for c in captures}
        
        total = 0
        for flag_id in captured_flags:
            flag = ALL_FLAGS.get(flag_id)
            if flag:
                total += flag.points
        
        return total
    
    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        """Get top scores leaderboard."""
        if settings.environment.value == "local":
            scores = {}
            for user_id, captures in self._local_captures.items():
                captured_flags = {c.flag_id for c in captures}
                total = sum(
                    ALL_FLAGS.get(fid, Flag("", FlagCategory.LLM01, "", FlagDifficulty.EASY, 0, "")).points
                    for fid in captured_flags
                )
                scores[user_id] = total
            
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return [
                {"user_id": uid, "score": score, "rank": i + 1}
                for i, (uid, score) in enumerate(sorted_scores[:limit])
            ]
        
        # For DynamoDB, we'd need a GSI or scan
        # Simplified for now
        return []
    
    def check_response_for_flags(
        self,
        response: str,
        user_id: str,
        method: str = "response_extraction",
    ) -> list[str]:
        """
        Check an LLM response for leaked flags and capture them.
        
        Args:
            response: LLM response text
            user_id: User who triggered the response
            method: Method of extraction
            
        Returns:
            List of captured flag IDs
        """
        captured = []
        
        matches = self.FLAG_PATTERN.findall(response)
        for match in matches:
            # Extract flag ID from FLAG{...}
            flag_id = match[5:-1]  # Strip FLAG{ and }
            
            # Check if it's a valid flag
            if flag_id in ALL_FLAGS:
                capture = self.capture(
                    flag_id=flag_id,
                    user_id=user_id,
                    method=method,
                    payload=response[:500],
                )
                if capture:
                    captured.append(flag_id)
        
        return captured
    
    def get_available_flags(self, service: str | None = None) -> list[dict]:
        """Get list of available flags (without revealing the actual flags)."""
        flags = ALL_FLAGS.values()
        if service:
            flags = [f for f in flags if f.service == service]
        
        return [
            {
                "flag_id": f.flag_id,
                "category": f.category.value,
                "difficulty": f.difficulty.value,
                "points": f.points,
                "description": f.description,
                "hint": f.hint,
            }
            for f in flags
        ]


# Global flag service instance
flag_service = FlagService()
