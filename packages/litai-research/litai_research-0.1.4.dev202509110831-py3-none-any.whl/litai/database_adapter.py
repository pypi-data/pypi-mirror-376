"""Database adapter for multi-user support with SQLite and Supabase backends."""

import os
from typing import Any

from litai.utils.logger import get_logger

from .config import Config
from .database import Database
from .models import Paper

logger = get_logger(__name__)


class DatabaseAdapter:
    """Adapter that provides unified interface for both SQLite and Supabase databases."""

    def __init__(self, config: Config | None = None):
        """Initialize database adapter based on environment.
        
        Args:
            config: Optional Config object, defaults to creating new one
        """
        self.config = config or Config()
        
        # Check if Supabase is configured
        if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
            self._init_supabase()
            self.mode = "supabase"
            logger.info("Database adapter initialized in Supabase mode")
        else:
            # Use local SQLite database
            self.db = Database(self.config)
            self.mode = "local"
            logger.info("Database adapter initialized in local SQLite mode")
    
    def _init_supabase(self) -> None:
        """Initialize Supabase client."""
        try:
            from supabase import create_client
            
            self.supabase = create_client(
                os.getenv("SUPABASE_URL", ""),
                os.getenv("SUPABASE_ANON_KEY", "")
            )
        except ImportError:
            logger.error("Supabase library not installed. Falling back to local mode.")
            self.db = Database(self.config)
            self.mode = "local"
    
    # Paper operations
    
    def add_paper(self, paper: Paper, user_id: str = "local") -> bool:
        """Add a paper to the database.
        
        Args:
            paper: Paper object to add
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            True if added successfully, False if already exists
        """
        if self.mode == "supabase":
            try:
                data = paper.to_dict()
                data["user_id"] = user_id
                
                result = self.supabase.table("papers").insert(data).execute()
                logger.info("Paper added to Supabase", paper_id=paper.paper_id, user_id=user_id)
                return True
            except Exception as e:
                logger.warning("Failed to add paper to Supabase", error=str(e))
                return False
        else:
            return self.db.add_paper(paper, user_id="local")
    
    def get_paper(self, paper_id: str, user_id: str = "local") -> Paper | None:
        """Get a paper by ID.
        
        Args:
            paper_id: ID of the paper
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            Paper object or None if not found
        """
        if self.mode == "supabase":
            try:
                result = self.supabase.table("papers").select("*").eq("paper_id", paper_id).eq("user_id", user_id).execute()
                if result.data:
                    return Paper.from_dict(result.data[0])
            except Exception as e:
                logger.error("Failed to get paper from Supabase", error=str(e))
                return None
        else:
            return self.db.get_paper(paper_id, user_id="local")
    
    def list_papers(
        self, 
        limit: int = 50, 
        offset: int = 0, 
        tag: str | None = None, 
        user_id: str = "local"
    ) -> list[Paper]:
        """List papers for a user.
        
        Args:
            limit: Maximum number of papers to return
            offset: Number of papers to skip
            tag: Optional tag to filter by
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            List of Paper objects
        """
        if self.mode == "supabase":
            try:
                query = self.supabase.table("papers").select("*").eq("user_id", user_id)
                
                if tag:
                    # For Supabase, we need to use contains for tag filtering
                    query = query.contains("tags", tag)
                
                query = query.order("added_at", desc=True).limit(limit).offset(offset)
                result = query.execute()
                
                papers = []
                for row in result.data:
                    paper = Paper.from_dict(row)
                    if row.get("tags"):
                        paper.tags = [t.strip() for t in row["tags"].split(",")]
                    papers.append(paper)
                return papers
            except Exception as e:
                logger.error("Failed to list papers from Supabase", error=str(e))
                return []
        else:
            return self.db.list_papers(limit, offset, tag, user_id="local")
    
    def count_papers(self, user_id: str = "local") -> int:
        """Count total papers for a user.
        
        Args:
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            Number of papers
        """
        if self.mode == "supabase":
            try:
                result = self.supabase.table("papers").select("*", count="exact").eq("user_id", user_id).execute()
                return result.count or 0
            except Exception as e:
                logger.error("Failed to count papers in Supabase", error=str(e))
                return 0
        else:
            return self.db.count_papers(user_id="local")
    
    def search_papers(self, query: str, user_id: str = "local") -> list[Paper]:
        """Search papers by title or abstract.
        
        Args:
            query: Search query
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            List of matching Paper objects
        """
        if self.mode == "supabase":
            try:
                # Use Supabase's text search capabilities
                result = self.supabase.table("papers").select("*").eq("user_id", user_id).or_(
                    f"title.ilike.%{query}%,abstract.ilike.%{query}%"
                ).order("citation_count", desc=True).limit(20).execute()
                
                papers = []
                for row in result.data:
                    paper = Paper.from_dict(row)
                    if row.get("tags"):
                        paper.tags = [t.strip() for t in row["tags"].split(",")]
                    papers.append(paper)
                return papers
            except Exception as e:
                logger.error("Failed to search papers in Supabase", error=str(e))
                return []
        else:
            return self.db.search_papers(query, user_id="local")
    
    def update_paper(self, paper_id: str, updates: dict, user_id: str = "local") -> bool:
        """Update multiple fields of a paper.
        
        Args:
            paper_id: ID of the paper to update
            updates: Dictionary of field names and values to update
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            True if updated successfully, False if paper not found
        """
        if self.mode == "supabase":
            try:
                result = self.supabase.table("papers").update(updates).eq("paper_id", paper_id).eq("user_id", user_id).execute()
                if result.data:
                    logger.info("Paper updated in Supabase", paper_id=paper_id, user_id=user_id, fields=list(updates.keys()))
                    return True
                return False
            except Exception as e:
                logger.error("Failed to update paper in Supabase", error=str(e))
                return False
        else:
            return self.db.update_paper(paper_id, updates, user_id="local")

    def delete_paper(self, paper_id: str, user_id: str = "local") -> bool:
        """Delete a paper.
        
        Args:
            paper_id: ID of the paper to delete
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            True if deleted, False if not found
        """
        if self.mode == "supabase":
            try:
                result = self.supabase.table("papers").delete().eq("paper_id", paper_id).eq("user_id", user_id).execute()
                if result.data:
                    logger.info("Paper deleted from Supabase", paper_id=paper_id, user_id=user_id)
                    return True
                return False
            except Exception as e:
                logger.error("Failed to delete paper from Supabase", error=str(e))
                return False
        else:
            return self.db.delete_paper(paper_id, user_id="local")
    
    # Note operations
    
    def add_note(self, paper_id: str, content: str, user_id: str = "local") -> bool:
        """Add or update notes for a paper.
        
        Args:
            paper_id: ID of the paper
            content: Note content
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            True if successful
        """
        if self.mode == "supabase":
            try:
                result = self.supabase.table("papers").update({"notes": content}).eq("paper_id", paper_id).eq("user_id", user_id).execute()
                logger.info("Note added to Supabase", paper_id=paper_id, user_id=user_id)
                return bool(result.data)
            except Exception as e:
                logger.error("Failed to add note to Supabase", error=str(e))
                return False
        else:
            return self.db.add_note(paper_id, content, user_id="local")
    
    def get_note(self, paper_id: str, user_id: str = "local") -> str | None:
        """Get notes for a paper.
        
        Args:
            paper_id: ID of the paper
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            Note content or None
        """
        if self.mode == "supabase":
            try:
                result = self.supabase.table("papers").select("notes").eq("paper_id", paper_id).eq("user_id", user_id).execute()
                if result.data and result.data[0].get("notes"):
                    return result.data[0]["notes"]
            except Exception as e:
                logger.error("Failed to get note from Supabase", error=str(e))
            return None
        else:
            return self.db.get_note(paper_id, user_id="local")
    
    # Tag operations
    
    def add_tags_to_paper(self, paper_id: str, tag_names: list[str], user_id: str = "local") -> None:
        """Add tags to a paper.
        
        Args:
            paper_id: ID of the paper
            tag_names: List of tag names to add
            user_id: User ID (defaults to 'local' for SQLite)
        """
        if self.mode == "supabase":
            try:
                # Get existing tags first
                result = self.supabase.table("papers").select("tags").eq("paper_id", paper_id).eq("user_id", user_id).execute()
                
                existing_tags = []
                if result.data and result.data[0].get("tags"):
                    existing_tags = [t.strip().lower() for t in result.data[0]["tags"].split(",")]
                
                # Add new tags
                new_tags = [t.lower().strip() for t in tag_names]
                all_tags = list(set(existing_tags + new_tags))
                tags_csv = ", ".join(sorted(all_tags))
                
                # Update
                self.supabase.table("papers").update({"tags": tags_csv}).eq("paper_id", paper_id).eq("user_id", user_id).execute()
                logger.info("Tags added to Supabase paper", paper_id=paper_id, tags=tag_names)
            except Exception as e:
                logger.error("Failed to add tags to Supabase", error=str(e))
        else:
            self.db.add_tags_to_paper(paper_id, tag_names, user_id="local")
    
    def get_paper_tags(self, paper_id: str, user_id: str = "local") -> list[str]:
        """Get tags for a paper.
        
        Args:
            paper_id: ID of the paper
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            List of tag names
        """
        if self.mode == "supabase":
            try:
                result = self.supabase.table("papers").select("tags").eq("paper_id", paper_id).eq("user_id", user_id).execute()
                if result.data and result.data[0].get("tags"):
                    return [t.strip() for t in result.data[0]["tags"].split(",")]
            except Exception as e:
                logger.error("Failed to get tags from Supabase", error=str(e))
            return []
        else:
            return self.db.get_paper_tags(paper_id, user_id="local")
    
    def list_all_tags(self, user_id: str = "local") -> list[tuple[str, int]]:
        """List all unique tags with counts for a user.
        
        Args:
            user_id: User ID (defaults to 'local' for SQLite)
            
        Returns:
            List of (tag_name, count) tuples
        """
        if self.mode == "supabase":
            try:
                result = self.supabase.table("papers").select("tags").eq("user_id", user_id).not_.is_("tags", "null").execute()
                
                tag_counts: dict[str, int] = {}
                for row in result.data:
                    if row.get("tags"):
                        for tag in row["tags"].split(","):
                            tag = tag.strip()
                            if tag:
                                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                return sorted(tag_counts.items())
            except Exception as e:
                logger.error("Failed to list tags from Supabase", error=str(e))
                return []
        else:
            return self.db.list_all_tags(user_id="local")
    
    # Full text operations
    
    def get_full_text(self, paper_id: str) -> str | None:
        """Get full text for a paper.
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            Full text content or None
        """
        if self.mode == "supabase":
            try:
                # For Supabase, full text might be stored in the database
                # or in a separate storage service
                result = self.supabase.table("papers").select("full_text").eq("paper_id", paper_id).execute()
                if result.data and result.data[0].get("full_text"):
                    return result.data[0]["full_text"]
            except Exception as e:
                logger.error("Failed to get full text from Supabase", error=str(e))
            return None
        else:
            return self.db.get_full_text(paper_id)
    
    # User operations (Supabase only)
    
    def get_user_api_key(self, user_id: str) -> str | None:
        """Get OpenAI API key for a user (Supabase only).
        
        Args:
            user_id: User ID
            
        Returns:
            API key or None
        """
        if self.mode == "supabase":
            try:
                result = self.supabase.table("users").select("openai_api_key").eq("user_id", user_id).execute()
                if result.data and result.data[0].get("openai_api_key"):
                    return result.data[0]["openai_api_key"]
            except Exception as e:
                logger.error("Failed to get user API key from Supabase", error=str(e))
        return None
    
    def set_user_api_key(self, user_id: str, api_key: str) -> bool:
        """Set OpenAI API key for a user (Supabase only).
        
        Args:
            user_id: User ID
            api_key: OpenAI API key
            
        Returns:
            True if successful
        """
        if self.mode == "supabase":
            try:
                # Try to update first
                result = self.supabase.table("users").update({"openai_api_key": api_key}).eq("user_id", user_id).execute()
                
                # If no rows updated, insert new user
                if not result.data:
                    result = self.supabase.table("users").insert({
                        "user_id": user_id,
                        "openai_api_key": api_key
                    }).execute()
                
                logger.info("User API key updated in Supabase", user_id=user_id)
                return True
            except Exception as e:
                logger.error("Failed to set user API key in Supabase", error=str(e))
                return False
        else:
            # In local mode, API key is managed by config
            logger.warning("Cannot set user API key in local mode")
            return False