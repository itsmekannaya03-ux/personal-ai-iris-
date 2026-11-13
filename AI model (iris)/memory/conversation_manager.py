"""
ConversationManager — Isolated Multi-Conversation & Person Chat System.

Manages persistent chat conversations for individual people, topics, and sessions.
Integrates with SQLite backend (`~/.iris/memory.db`) with full message history,
provider metadata tracking (online vs offline), and search.
"""

import time
import uuid
import json
import logging
from typing import Optional, List, Dict, Any
from memory.db import DatabaseManager

logger = logging.getLogger("iris.conversation_manager")


class ConversationManager:
    """Manages conversations and message histories stored in SQLite."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def create_conversation(
        self,
        title: str = "New Chat",
        person_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new conversation session."""
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        now = time.time()
        meta_json = json.dumps(metadata or {})

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversations (id, title, person_name, system_prompt, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (conv_id, title.strip() or "New Chat", person_name.strip() if person_name else None, system_prompt, now, now, meta_json),
            )
            conn.commit()

        logger.info(f"Created conversation '{title}' (id={conv_id}, person={person_name})")
        return {
            "id": conv_id,
            "title": title,
            "person_name": person_name,
            "system_prompt": system_prompt,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
            "message_count": 0,
            "last_message": None,
        }

    def list_conversations(
        self,
        search: Optional[str] = None,
        person_name: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List conversations ordered by most recently updated."""
        query = """
            SELECT c.*, 
                   COUNT(m.id) as msg_count,
                   (SELECT content FROM conversation_messages WHERE conversation_id = c.id ORDER BY timestamp DESC LIMIT 1) as last_content,
                   (SELECT role FROM conversation_messages WHERE conversation_id = c.id ORDER BY timestamp DESC LIMIT 1) as last_role,
                   (SELECT timestamp FROM conversation_messages WHERE conversation_id = c.id ORDER BY timestamp DESC LIMIT 1) as last_msg_time
            FROM conversations c
            LEFT JOIN conversation_messages m ON c.id = m.conversation_id
            WHERE 1=1
        """
        params: List[Any] = []

        if person_name:
            query += " AND LOWER(c.person_name) = LOWER(?)"
            params.append(person_name.strip())

        if search:
            query += " AND (LOWER(c.title) LIKE LOWER(?) OR LOWER(c.person_name) LIKE LOWER(?))"
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern])

        query += " GROUP BY c.id ORDER BY c.updated_at DESC LIMIT ?"
        params.append(limit)

        results = []
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                meta = {}
                if row["metadata"]:
                    try:
                        meta = json.loads(row["metadata"])
                    except Exception:
                        pass
                results.append({
                    "id": row["id"],
                    "title": row["title"],
                    "person_name": row["person_name"],
                    "system_prompt": row["system_prompt"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": meta,
                    "message_count": row["msg_count"],
                    "last_message": {
                        "role": row["last_role"],
                        "content": row["last_content"],
                        "timestamp": row["last_msg_time"],
                    } if row["last_content"] else None,
                })
        return results

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        """Fetch conversation details by ID."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
            row = cursor.fetchone()
            if not row:
                return None
            meta = {}
            if row["metadata"]:
                try:
                    meta = json.loads(row["metadata"])
                except Exception:
                    pass
            return {
                "id": row["id"],
                "title": row["title"],
                "person_name": row["person_name"],
                "system_prompt": row["system_prompt"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": meta,
            }

    def get_or_create_person_chat(self, person_name: str) -> Dict[str, Any]:
        """Find or create a distinct conversation thread for an individual person."""
        clean_name = person_name.strip()
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM conversations WHERE LOWER(person_name) = LOWER(?) ORDER BY updated_at DESC LIMIT 1",
                (clean_name,),
            )
            row = cursor.fetchone()
            if row:
                return self.get_conversation(row["id"])

        # Create new dedicated person chat
        title = f"{clean_name.title()} Chat"
        system_prompt = f"You are IRIS conversing with or about {clean_name.title()}. Keep context personalized and empathetic."
        return self.create_conversation(title=title, person_name=clean_name, system_prompt=system_prompt)

    def get_active_or_default_conversation(self) -> Dict[str, Any]:
        """Retrieve most recently active conversation or initialize General Chat."""
        convs = self.list_conversations(limit=1)
        if convs:
            return convs[0]
        return self.create_conversation(title="General Chat", person_name=None)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        is_offline: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append a message to a conversation thread and update timestamp."""
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = time.time()
        meta_json = json.dumps(metadata or {})

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            # Ensure conversation exists
            cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
            if not cursor.fetchone():
                # Auto-create if somehow missing
                self.create_conversation(title="Active Session")

            cursor.execute(
                """
                INSERT INTO conversation_messages 
                (id, conversation_id, role, content, provider, model, is_offline, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (msg_id, conversation_id, role, content, provider, model, 1 if is_offline else 0, now, meta_json),
            )
            cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
            conn.commit()

        return {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "provider": provider,
            "model": model,
            "is_offline": bool(is_offline),
            "timestamp": now,
            "metadata": metadata or {},
        }

    def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve chronological message history for a conversation."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM (
                    SELECT * FROM conversation_messages 
                    WHERE conversation_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ) ORDER BY timestamp ASC
                """,
                (conversation_id, limit),
            )
            results = []
            for row in cursor.fetchall():
                meta = {}
                if row["metadata"]:
                    try:
                        meta = json.loads(row["metadata"])
                    except Exception:
                        pass
                results.append({
                    "id": row["id"],
                    "conversation_id": row["conversation_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "provider": row["provider"],
                    "model": row["model"],
                    "is_offline": bool(row["is_offline"]),
                    "timestamp": row["timestamp"],
                    "metadata": meta,
                })
            return results

    def rename_conversation(self, conversation_id: str, new_title: str) -> bool:
        """Rename a conversation."""
        if not new_title.strip():
            return False
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (new_title.strip(), time.time(), conversation_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its messages."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_messages WHERE conversation_id = ?", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            return cursor.rowcount > 0

    def search_messages(self, query: str, conversation_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search message content across one or all conversations."""
        sql = """
            SELECT m.*, c.title as conv_title, c.person_name
            FROM conversation_messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE LOWER(m.content) LIKE LOWER(?)
        """
        params: List[Any] = [f"%{query.strip()}%"]
        if conversation_id:
            sql += " AND m.conversation_id = ?"
            params.append(conversation_id)

        sql += " ORDER BY m.timestamp DESC LIMIT ?"
        params.append(limit)

        results = []
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "conversation_id": row["conversation_id"],
                    "conversation_title": row["conv_title"],
                    "person_name": row["person_name"],
                    "role": row["role"],
                    "content": row["content"],
                    "provider": row["provider"],
                    "model": row["model"],
                    "is_offline": bool(row["is_offline"]),
                    "timestamp": row["timestamp"],
                })
        return results


_conv_mgr_instance: Optional[ConversationManager] = None

def get_conversation_manager() -> ConversationManager:
    """Singleton getter for ConversationManager."""
    global _conv_mgr_instance
    if _conv_mgr_instance is None:
        _conv_mgr_instance = ConversationManager()
    return _conv_mgr_instance
