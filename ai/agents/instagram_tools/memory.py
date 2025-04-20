"""
Memory Layer for Instagram Agent

This module stores facts or states about the users or the environment
that may be relevant for future reasoning.
"""

import logging
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger("insta-memory")

class AgentMemory:
    """
    Memory class for the Instagram agent to store and recall information
    """
    
    def __init__(self):
        """Initialize the memory with empty collections"""
        self.users_metrics = []  # Store metrics for each user
        self.iteration_responses = []  # Store responses from each iteration
        self.processed_usernames = set()  # Track which usernames have been processed
        self.scored_users = set()  # Track which users have been scored
        
    def store_user_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Store metrics for a user
        
        Args:
            metrics: Dictionary containing user metrics
        """
        username = metrics.get("username")
        if not username:
            logger.warning("Attempted to store metrics without username")
            return
            
        # Check if user already exists in memory
        for i, existing in enumerate(self.users_metrics):
            if existing.get("username") == username:
                # Update existing user
                self.users_metrics[i] = metrics
                logger.info(f"Updated metrics for user: {username}")
                return
                
        # Add new user
        self.users_metrics.append(metrics)
        self.processed_usernames.add(username)
        logger.info(f"Stored metrics for new user: {username}")
        
    def store_user_score(self, username: str, score: float) -> None:
        """
        Store score for a user
        
        Args:
            username: Username of the user
            score: Calculated score
        """
        for i, user in enumerate(self.users_metrics):
            if user.get("username") == username:
                self.users_metrics[i]["score"] = score
                self.scored_users.add(username)
                logger.info(f"Stored score {score} for user: {username}")
                return
                
        logger.warning(f"Attempted to store score for unknown user: {username}")
        
    def update_users_list(self, users_list: List[Dict[str, Any]]) -> None:
        """
        Update the entire users metrics list
        
        Args:
            users_list: New list of user metrics
        """
        self.users_metrics = users_list
        logger.info(f"Updated users list with {len(users_list)} users")
        
    def add_iteration_response(self, response: str) -> None:
        """
        Add a response from an iteration
        
        Args:
            response: The response string
        """
        self.iteration_responses.append(response)
        
    def get_user_metrics(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a specific user
        
        Args:
            username: Username to retrieve
            
        Returns:
            User metrics or None if not found
        """
        for user in self.users_metrics:
            if user.get("username") == username:
                return user
        return None
        
    def get_all_users_metrics(self) -> List[Dict[str, Any]]:
        """
        Get metrics for all users
        
        Returns:
            List of all user metrics
        """
        return self.users_metrics
        
    def get_iteration_responses(self) -> List[str]:
        """
        Get all iteration responses
        
        Returns:
            List of iteration response strings
        """
        return self.iteration_responses
        
    def get_unprocessed_usernames(self, all_usernames: List[str]) -> List[str]:
        """
        Get usernames that haven't been processed yet
        
        Args:
            all_usernames: List of all usernames to check against
            
        Returns:
            List of unprocessed usernames
        """
        return [u for u in all_usernames if u not in self.processed_usernames]
        
    def get_unscored_users(self) -> List[Dict[str, Any]]:
        """
        Get users that haven't been scored yet
        
        Returns:
            List of unscored user metrics
        """
        return [u for u in self.users_metrics if u.get("username") not in self.scored_users]
        
    def all_users_processed(self, all_usernames: List[str]) -> bool:
        """
        Check if all users have been processed
        
        Args:
            all_usernames: List of all usernames to check against
            
        Returns:
            True if all users have been processed
        """
        return all(u in self.processed_usernames for u in all_usernames)
        
    def all_users_scored(self) -> bool:
        """
        Check if all users have been scored
        
        Returns:
            True if all users have been scored
        """
        return all(u.get("username") in self.scored_users for u in self.users_metrics)
        
    def get_context_dict(self) -> Dict[str, Any]:
        """
        Get a dictionary representation of the memory for context
        
        Returns:
            Dictionary with memory contents
        """
        return {
            "users_metrics_list": self.users_metrics,
            "iteration_responses": self.iteration_responses,
            "processed_usernames": list(self.processed_usernames),
            "scored_users": list(self.scored_users)
        }