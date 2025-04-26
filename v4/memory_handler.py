"""
Memory Handler for Chat Agent

This module implements a memory handler that stores chat history in Supabase,
allowing dynamic retrieval based on user identifier.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain.schema import BaseChatMessageHistory, AIMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import ChatMessageHistory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SupabaseChatMessageHistory(BaseChatMessageHistory):
    """Chat message history that stores messages in Supabase."""
    
    def __init__(self, user_id: str, table_name: str = "chat_history"):
        """
        Initialize with Supabase client and user_id.
        
        Args:
            user_id: Unique identifier for the user (username, phone number)
            table_name: Name of the Supabase table to use
        """
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.table_name = table_name
        self.user_id = user_id
        
        # Ensure table exists with required schema
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """Ensure the chat_history table exists in Supabase."""
        try:
            # Check if table exists by attempting to fetch a single row
            self.supabase.table(self.table_name).select("id").limit(1).execute()
            logger.info(f"Table {self.table_name} exists")
        except Exception as e:
            logger.error(f"Error checking table {self.table_name}: {e}")
            logger.warning("Please create the following table in Supabase:")
            logger.warning("""
            CREATE TABLE public.chat_history (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                messages JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            CREATE INDEX idx_chat_history_user_id ON public.chat_history (user_id);
            """)
    
    def _get_messages_dict(self) -> Dict[str, Any]:
        """Get user's messages dictionary from Supabase."""
        try:
            response = self.supabase.table(self.table_name) \
                .select("messages") \
                .eq("user_id", self.user_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching messages for user {self.user_id}: {e}")
            return None
    
    def _save_messages_dict(self, messages_dict: List[Dict[str, Any]]) -> None:
        """Save messages dictionary to Supabase."""
        try:
            # Check if record exists for user
            existing_record = self._get_messages_dict()
            
            if existing_record:
                # Update existing record
                self.supabase.table(self.table_name) \
                    .update({"messages": messages_dict, "updated_at": "NOW()"}) \
                    .eq("user_id", self.user_id) \
                    .execute()
            else:
                # Insert new record
                self.supabase.table(self.table_name) \
                    .insert({
                        "user_id": self.user_id,
                        "messages": messages_dict
                    }) \
                    .execute()
            
            logger.debug(f"Saved {len(messages_dict)} messages for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error saving messages for user {self.user_id}: {e}")
    
    @property
    def messages(self) -> List[HumanMessage | AIMessage]:
        """Get messages from Supabase."""
        result = []
        record = self._get_messages_dict()
        
        if not record or not record.get("messages"):
            return result
        
        for message_dict in record.get("messages", []):
            if message_dict.get("type") == "human":
                result.append(HumanMessage(content=message_dict.get("content", "")))
            elif message_dict.get("type") == "ai":
                result.append(AIMessage(content=message_dict.get("content", "")))
        
        return result
    
    def add_user_message(self, message: str) -> None:
        """Add a user message to the history."""
        self.add_message(HumanMessage(content=message))
    
    def add_ai_message(self, message: str) -> None:
        """Add an AI message to the history."""
        self.add_message(AIMessage(content=message))
    
    def add_message(self, message: HumanMessage | AIMessage) -> None:
        """Add a message to the history."""
        messages_dicts = []
        
        # Convert existing messages to dicts
        for msg in self.messages:
            message_type = "human" if isinstance(msg, HumanMessage) else "ai"
            messages_dicts.append({
                "type": message_type,
                "content": msg.content
            })
        
        # Add new message
        message_type = "human" if isinstance(message, HumanMessage) else "ai"
        messages_dicts.append({
            "type": message_type,
            "content": message.content
        })
        
        # Save to Supabase
        self._save_messages_dict(messages_dicts)
    
    def clear(self) -> None:
        """Clear the message history."""
        try:
            self.supabase.table(self.table_name) \
                .delete() \
                .eq("user_id", self.user_id) \
                .execute()
            
            logger.info(f"Cleared message history for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error clearing messages for user {self.user_id}: {e}")

class DynamicMemoryHandler:
    """Handler for dynamic memory management across multiple users."""
    
    def __init__(self):
        """Initialize the memory handler."""
        self.memories = {}  # Cache of memory objects
    
    def get_memory(self, user_id: str) -> ConversationBufferMemory:
        """
        Get a memory object for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            ConversationBufferMemory: Memory for the user
        """
        if user_id not in self.memories:
            logger.info(f"Creating new memory for user {user_id}")
            message_history = SupabaseChatMessageHistory(user_id=user_id)
            memory = ConversationBufferMemory(
                chat_memory=message_history,
                return_messages=True,
                memory_key="chat_history"
            )
            self.memories[user_id] = memory
        
        return self.memories[user_id]
    
    def clear_memory(self, user_id: str) -> None:
        """
        Clear memory for a user.
        
        Args:
            user_id: Unique identifier for the user
        """
        if user_id in self.memories:
            self.memories[user_id].chat_memory.clear()
            logger.info(f"Cleared memory for user {user_id}") 