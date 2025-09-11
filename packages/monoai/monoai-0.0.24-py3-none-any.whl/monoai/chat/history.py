import os
import json
import uuid
import sqlite3
from monoai.models import Model
import datetime

class BaseHistory:

    def __init__(self, 
                 path: str, 
                 last_n: int=None): 
        self._history_path = path
        self._last_n = last_n
        
    def generate_chat_id(self):
        return str(uuid.uuid4())

    def load(self):
        pass

    def store(self, chat_id: str, messages: list):
        # Aggiungi un timestamp ISO 8601 a ciascun messaggio
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        for msg in messages:
            if 'timestamp' not in msg:
                msg['timestamp'] = now
        return messages

    def clear(self):
        pass


class JSONHistory(BaseHistory):
    
    def __init__(self, 
                 path, 
                 last_n: int=None): 
        self._history_path = path
        self._last_n = last_n
        if not os.path.exists(self._history_path):
            os.makedirs(self._history_path)

    def load(self, chat_id: str):
        # Ensure proper path construction with os.path.join
        file_path = os.path.join(self._history_path, chat_id + ".json")
        with open(file_path, "r") as f:
            self.messages = json.load(f)
        if self._last_n is not None and len(self.messages) > (self._last_n+1)*2:
            self.messages = [self.messages[0]]+self.messages[-self._last_n*2:]
        return self.messages
    
    def new(self, system_prompt: str):
        chat_id = self.generate_chat_id()
        # Ensure directory exists before storing
        if not os.path.exists(self._history_path):
            os.makedirs(self._history_path, exist_ok=True)
        self.store(chat_id, [{"role": "system", "content": system_prompt}])
        return chat_id

    def store(self, chat_id: str, messages: list):
        messages = super().store(chat_id, messages)
        # Load existing messages
        file_path = os.path.join(self._history_path, chat_id + ".json")
        try:
            with open(file_path, "r") as f:
                existing_messages = json.load(f)
        except FileNotFoundError:
            existing_messages = []
        
        # Add the new messages (già con timestamp)
        new_messages = existing_messages + messages
        
        with open(file_path, "w") as f:
            json.dump(new_messages, f, indent=4)

class SQLiteHistory(BaseHistory):
    
    def __init__(self, path: str="histories/chat.db", last_n: int=None):
        self._db_path = path
        self._last_n = last_n
        self._init_db()
    
    def _init_db(self):
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    chat_id TEXT,
                    order_index INTEGER,
                    role TEXT,
                    content TEXT,
                    PRIMARY KEY (chat_id, order_index)
                )
            """)
    
    def load(self, chat_id: str):
        with sqlite3.connect(self._db_path) as conn:
            if self._last_n is not None:
                # Get system message
                cursor = conn.execute(
                    "SELECT role, content FROM messages WHERE chat_id = ? AND order_index = 0",
                    (chat_id,)
                )
                system_message = cursor.fetchone()
                
                # Get last N messages
                cursor = conn.execute(
                    """
                    SELECT role, content 
                    FROM messages 
                    WHERE chat_id = ? 
                    ORDER BY order_index DESC 
                    LIMIT ?
                    """,
                    (chat_id, self._last_n * 2)
                )
                last_messages = [{"role": role, "content": content} for role, content in cursor]
                last_messages.reverse()  # Reverse to get correct order
                
                # Combine system message with last N messages
                self.messages = [{"role": system_message[0], "content": system_message[1]}] + last_messages
            else:
                cursor = conn.execute(
                    "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY order_index",
                    (chat_id,)
                )
                self.messages = [{"role": role, "content": content} for role, content in cursor]
        return self.messages
    
    def new(self, system_prompt: str):
        chat_id = self.generate_chat_id()
        self.store(chat_id, [{"role": "system", "content": system_prompt, "order_index": 0}])
        return chat_id

    def store(self, chat_id: str, messages: list):
        messages = super().store(chat_id, messages)
        with sqlite3.connect(self._db_path) as conn:
            # Get the last order_index
            cursor = conn.execute(
                "SELECT MAX(order_index) FROM messages WHERE chat_id = ?",
                (chat_id,)
            )
            last_index = cursor.fetchone()[0]
            
            # If no messages exist yet, start from -1
            if last_index is None:
                last_index = -1
            
            # Insert the new messages con timestamp
            for i, message in enumerate(messages, start=last_index + 1):
                conn.execute(
                    "INSERT INTO messages (chat_id, order_index, role, content) VALUES (?, ?, ?, ?)",
                    (chat_id, i, message["role"], message["content"])
                )
                conn.commit()
        

class DictHistory(BaseHistory):
    """
    In-memory history storage using Python dictionaries.
    Useful for testing and temporary conversations.
    """
    
    def __init__(self, last_n: int = None):
        self._last_n = last_n
        self._histories = {}  # Dictionary to store chat histories
    
    def load(self, chat_id: str):
        if chat_id not in self._histories:
            self.messages = []
            return self.messages
        
        messages = self._histories[chat_id]
        if self._last_n is not None and len(messages) > (self._last_n + 1) * 2:
            messages = [messages[0]] + messages[-self._last_n * 2:]
        
        self.messages = messages
        return self.messages
    
    def new(self, system_prompt: str):
        chat_id = self.generate_chat_id()
        messages = [{"role": "system", "content": system_prompt}]
        self.store(chat_id, messages)
        return chat_id
    
    def store(self, chat_id: str, messages: list):
        messages = super().store(chat_id, messages)
        
        if chat_id not in self._histories:
            self._histories[chat_id] = []
        
        # Add the new messages (già con timestamp)
        self._histories[chat_id].extend(messages)
    
    def clear(self, chat_id: str):
        """Clear history for a specific chat."""
        if chat_id in self._histories:
            del self._histories[chat_id]
    
    def clear_all(self):
        """Clear all chat histories."""
        self._histories.clear()
    
    def get_all_chat_ids(self):
        """Get all chat IDs currently stored."""
        return list(self._histories.keys())
    
    def get_chat_count(self):
        """Get the total number of chats stored."""
        return len(self._histories)


class MongoDBHistory(BaseHistory):
    def __init__(self, db_path, db_name: str = "chat", collection_name: str = "histories", last_n: int = None):

        try:
            from pymongo import MongoClient
        except ImportError:
            raise ImportError("pymongo is not installed. Please install it with 'pip install pymongo'")

        self._uri = db_path
        self._db_name = db_name
        self._collection_name = collection_name
        self._last_n = last_n
        self._client = MongoClient(self._uri)
        self._db = self._client[self._db_name]
        self._collection = self._db[self._collection_name]

    def load(self, chat_id: str):
        doc = self._collection.find_one({"chat_id": chat_id})
        if not doc:
            self.messages = []
            return self.messages
        messages = doc.get("messages", [])
        if self._last_n is not None and len(messages) > (self._last_n + 1) * 2:
            messages = [messages[0]] + messages[-self._last_n * 2:]
        self.messages = messages
        return self.messages

    def new(self, system_prompt: str):
        chat_id = self.generate_chat_id()
        messages = [{"role": "system", "content": system_prompt}]
        self.store(chat_id, messages)
        return chat_id

    def store(self, chat_id: str, messages: list):
        messages = super().store(chat_id, messages)
        # Get existing messages
        doc = self._collection.find_one({"chat_id": chat_id})
        existing_messages = doc.get("messages", []) if doc else []
        
        # Add the new messages (già con timestamp)
        new_messages = existing_messages + messages
        
        self._collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"messages": new_messages}},
            upsert=True
        )


class FirestoreHistory(BaseHistory):
    """Firestore-based history storage using Google Cloud Firestore.
    
    This class provides persistent storage for chat histories using Google Cloud Firestore,
    a NoSQL document database that scales automatically and provides real-time updates.
    
    Attributes
    ----------
    _collection_name : str
        Name of the Firestore collection to store chat histories
    _last_n : Optional[int]
        Maximum number of recent messages to load
    _client : Any
        Firestore client instance
    _collection : Any
        Firestore collection reference
    """
    
    def __init__(self, collection_name: str = "chat_histories", 
                 credentials_path: str = None, last_n: int = None):
        """Initialize Firestore history storage.
        
        Parameters
        ----------
        collection_name : str, optional
            Name of the Firestore collection (default: "chat_histories")
        credentials_path : str, optional
            Path to Google Cloud service account credentials JSON file
        last_n : int, optional
            Maximum number of recent messages to load (default: None for all messages)
        """
        super().__init__(path="firestore", last_n=last_n)
        self._collection_name = collection_name
        self._credentials_path = credentials_path
        self._client = None
        self._collection = None
        self._init_firestore()
    
    def _init_firestore(self):
        """Initialize Firestore client and collection reference."""
        try:
            import google.cloud.firestore as firestore
            
            if self._credentials_path and os.path.exists(self._credentials_path):
                # Use service account credentials
                import google.auth
                from google.oauth2 import service_account
                
                credentials = service_account.Credentials.from_service_account_file(
                    self._credentials_path
                )
                # Project ID is extracted from credentials
                self._client = firestore.Client(credentials=credentials)
            else:
                # Use default credentials (from environment or metadata server)
                self._client = firestore.Client()
            
            self._collection = self._client.collection(self._collection_name)
            
        except ImportError:
            raise ImportError(
                "google-cloud-firestore is required for FirestoreHistory. "
                "Install it with: pip install google-cloud-firestore"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Firestore: {e}")

    def load(self, chat_id: str):
        """Load chat history from Firestore.
        
        Parameters
        ----------
        chat_id : str
            Unique identifier for the chat
            
        Returns
        -------
        list
            List of messages in the chat history
        """
        try:
            doc_ref = self._collection.document(chat_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                self.messages = []
                return self.messages
            
            data = doc.to_dict()
            messages = data.get("messages", [])
            
            # Apply last_n filter if specified
            if self._last_n is not None and len(messages) > (self._last_n + 1) * 2:
                messages = [messages[0]] + messages[-self._last_n * 2:]
            
            self.messages = messages
            return self.messages
            
        except Exception as e:
            # Log error and return empty messages
            print(f"Error loading from Firestore: {e}")
            self.messages = []
            return self.messages
    
    def new(self, system_prompt: str):
        """Create a new chat with system prompt.
        
        Parameters
        ----------
        system_prompt : str
            System prompt for the new chat
            
        Returns
        -------
        str
            Generated chat ID
        """
        chat_id = self.generate_chat_id()
        messages = [{"role": "system", "content": system_prompt}]
        self.store(chat_id, messages)
        return chat_id
    

    def store(self, chat_id: str, messages: list):
        """Store messages in Firestore.
        
        Parameters
        ----------
        chat_id : str
            Unique identifier for the chat
        messages : list
            List of messages to store
        """
        # Add timestamps to messages
        messages = super().store(chat_id, messages)
        
        try:
            doc_ref = self._collection.document(chat_id)
            
            # Get existing messages
            doc = doc_ref.get()
            existing_messages = []
            
            if doc.exists:
                data = doc.to_dict()
                existing_messages = data.get("messages", [])
            
            # Add new messages
            new_messages = existing_messages + messages
            
            # Update document with new messages
            doc_ref.set({
                "chat_id": chat_id,
                "messages": new_messages,
                "last_updated": datetime.datetime.utcnow().isoformat() + 'Z',
                "message_count": len(new_messages)
            }, merge=True)
            
        except Exception as e:
            print(f"Error storing to Firestore: {e}")
            raise RuntimeError(f"Failed to store messages: {e}")
            

    def clear(self, chat_id: str = None):
        """Clear chat history.
        
        Parameters
        ----------
        chat_id : str, optional
            Specific chat ID to clear. If None, clears all chats.
        """
        try:
            if chat_id:
                # Clear specific chat
                doc_ref = self._collection.document(chat_id)
                doc_ref.delete()
            else:
                # Clear all chats
                docs = self._collection.stream()
                for doc in docs:
                    doc.reference.delete()
                    
        except Exception as e:
            print(f"Error clearing from Firestore: {e}")
    
    def get_all_chat_ids(self):
        """Get all chat IDs currently stored.
        
        Returns
        -------
        list
            List of all chat IDs
        """
        try:
            docs = self._collection.stream()
            return [doc.id for doc in docs]
        except Exception as e:
            print(f"Error getting chat IDs from Firestore: {e}")
            return []
    
    def get_chat_count(self):
        """Get the total number of chats stored.
        
        Returns
        -------
        int
            Total number of chats
        """
        try:
            docs = self._collection.stream()
            return len(list(docs))
        except Exception as e:
            print(f"Error getting chat count from Firestore: {e}")
            return 0
    
    def search_messages(self, query: str, limit: int = 10):
        """Search for messages containing specific text.
        
        Parameters
        ----------
        query : str
            Text to search for in messages
        limit : int, optional
            Maximum number of results to return (default: 10)
            
        Returns
        -------
        list
            List of matching messages with chat_id and message details
        """
        try:
            # Note: Firestore doesn't support full-text search natively
            # This is a simple substring search implementation
            # For production use, consider using Algolia or similar search service
            
            results = []
            docs = self._collection.stream()
            
            for doc in docs:
                data = doc.to_dict()
                messages = data.get("messages", [])
                
                for msg in messages:
                    if query.lower() in msg.get("content", "").lower():
                        results.append({
                            "chat_id": doc.id,
                            "message": msg,
                            "timestamp": msg.get("timestamp")
                        })
                        
                        if len(results) >= limit:
                            break
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            print(f"Error searching messages in Firestore: {e}")
            return []
    
    def get_chat_metadata(self, chat_id: str):
        """Get metadata about a specific chat.
        
        Parameters
        ----------
        chat_id : str
            Unique identifier for the chat
            
        Returns
        -------
        dict
            Dictionary containing chat metadata
        """
        try:
            doc_ref = self._collection.document(chat_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            return {
                "chat_id": chat_id,
                "message_count": data.get("message_count", 0),
                "last_updated": data.get("last_updated"),
                "created_at": data.get("created_at")
            }
            
        except Exception as e:
            print(f"Error getting chat metadata from Firestore: {e}")
            return None
    
    def close(self):
        """Close Firestore client connection."""
        if self._client:
            self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class HistorySummarizer():

    def __init__(self, model: Model, max_tokens: int=None):
        self._model = model
        self._max_tokens = max_tokens

    def summarize(self, messages: list):
        response = self._model.ask("Summarize the following conversation: "+json.dumps(messages))
        response = response["response"]
        return response

