"""
Unified Database Adapter for AWS WAF Scanner Enterprise
========================================================
Provides a single interface for multiple database backends.

Supported backends:
- Firebase Realtime Database
- Firestore
- SQLite (local/development)
- In-memory (testing)

Usage:
    from database_adapter import get_database, DatabaseConfig
    
    db = get_database()
    db.save_assessment(assessment_data)
    assessment = db.get_assessment(assessment_id)
"""

import os
import json
import sqlite3
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import threading

from logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class DatabaseBackend(Enum):
    """Supported database backends"""
    FIREBASE = "firebase"
    FIRESTORE = "firestore"
    SQLITE = "sqlite"
    MEMORY = "memory"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    backend: DatabaseBackend = DatabaseBackend.SQLITE
    
    # SQLite settings
    sqlite_path: str = "data/waf_scanner.db"
    
    # Firebase settings
    firebase_url: str = ""
    firebase_credentials: Dict = None
    
    # Firestore settings
    firestore_project: str = ""
    firestore_credentials: Dict = None
    
    # General settings
    connection_timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create configuration from environment variables"""
        backend_str = os.environ.get('DB_BACKEND', 'sqlite').lower()
        backend = DatabaseBackend(backend_str) if backend_str in [b.value for b in DatabaseBackend] else DatabaseBackend.SQLITE
        
        return cls(
            backend=backend,
            sqlite_path=os.environ.get('SQLITE_PATH', 'data/waf_scanner.db'),
            firebase_url=os.environ.get('FIREBASE_URL', ''),
            firestore_project=os.environ.get('FIRESTORE_PROJECT', ''),
        )


# ============================================================================
# ABSTRACT BASE CLASS
# ============================================================================

class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to database"""
        pass
    
    # Assessment operations
    @abstractmethod
    def save_assessment(self, assessment: Dict) -> str:
        """Save an assessment, returns assessment ID"""
        pass
    
    @abstractmethod
    def get_assessment(self, assessment_id: str) -> Optional[Dict]:
        """Get assessment by ID"""
        pass
    
    @abstractmethod
    def list_assessments(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """List assessments, optionally filtered by user"""
        pass
    
    @abstractmethod
    def delete_assessment(self, assessment_id: str) -> bool:
        """Delete an assessment"""
        pass
    
    # User operations
    @abstractmethod
    def save_user(self, user: Dict) -> str:
        """Save a user, returns user ID"""
        pass
    
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        pass
    
    @abstractmethod
    def list_users(self, limit: int = 100) -> List[Dict]:
        """List all users"""
        pass
    
    # Scan history operations
    @abstractmethod
    def save_scan_result(self, scan_result: Dict) -> str:
        """Save a scan result, returns scan ID"""
        pass
    
    @abstractmethod
    def get_scan_result(self, scan_id: str) -> Optional[Dict]:
        """Get scan result by ID"""
        pass
    
    @abstractmethod
    def list_scan_results(self, account_id: str = None, limit: int = 100) -> List[Dict]:
        """List scan results, optionally filtered by account"""
        pass


# ============================================================================
# SQLITE ADAPTER
# ============================================================================

class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter for local/development use"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db_path = config.sqlite_path
        self._connection = None
        self._lock = threading.Lock()
        
    def connect(self) -> bool:
        """Establish database connection and create tables"""
        try:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=self.config.connection_timeout
            )
            self._connection.row_factory = sqlite3.Row
            
            # Create tables
            self._create_tables()
            
            logger.info(f"Connected to SQLite database: {self.db_path}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnected from SQLite database")
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connection is not None
    
    def _create_tables(self):
        """Create database tables"""
        with self._lock:
            cursor = self._connection.cursor()
            
            # Assessments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    workload_name TEXT,
                    account_id TEXT,
                    status TEXT,
                    overall_score REAL,
                    data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    name TEXT,
                    role TEXT DEFAULT 'user',
                    data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Scan results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_results (
                    id TEXT PRIMARY KEY,
                    account_id TEXT,
                    regions TEXT,
                    total_findings INTEGER,
                    critical_count INTEGER,
                    high_count INTEGER,
                    medium_count INTEGER,
                    low_count INTEGER,
                    data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assessments_user ON assessments(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assessments_account ON assessments(account_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_results_account ON scan_results(account_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            
            self._connection.commit()
    
    def _generate_id(self, prefix: str = '') -> str:
        """Generate a unique ID"""
        import uuid
        return f"{prefix}{uuid.uuid4().hex[:16]}"
    
    # Assessment operations
    def save_assessment(self, assessment: Dict) -> str:
        """Save an assessment"""
        with self._lock:
            cursor = self._connection.cursor()
            
            assessment_id = assessment.get('id') or self._generate_id('asmt_')
            now = datetime.utcnow().isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO assessments 
                (id, user_id, workload_name, account_id, status, overall_score, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                assessment_id,
                assessment.get('user_id'),
                assessment.get('workload_name'),
                assessment.get('account_id'),
                assessment.get('status', 'draft'),
                assessment.get('overall_score', 0),
                json.dumps(assessment),
                assessment.get('created_at', now),
                now
            ))
            
            self._connection.commit()
            logger.debug(f"Saved assessment: {assessment_id}")
            return assessment_id
    
    def get_assessment(self, assessment_id: str) -> Optional[Dict]:
        """Get assessment by ID"""
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute('SELECT data FROM assessments WHERE id = ?', (assessment_id,))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row['data'])
            return None
    
    def list_assessments(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """List assessments"""
        with self._lock:
            cursor = self._connection.cursor()
            
            if user_id:
                cursor.execute(
                    'SELECT data FROM assessments WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?',
                    (user_id, limit)
                )
            else:
                cursor.execute(
                    'SELECT data FROM assessments ORDER BY updated_at DESC LIMIT ?',
                    (limit,)
                )
            
            return [json.loads(row['data']) for row in cursor.fetchall()]
    
    def delete_assessment(self, assessment_id: str) -> bool:
        """Delete an assessment"""
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute('DELETE FROM assessments WHERE id = ?', (assessment_id,))
            self._connection.commit()
            return cursor.rowcount > 0
    
    # User operations
    def save_user(self, user: Dict) -> str:
        """Save a user"""
        with self._lock:
            cursor = self._connection.cursor()
            
            user_id = user.get('id') or self._generate_id('user_')
            
            cursor.execute('''
                INSERT OR REPLACE INTO users (id, email, name, role, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                user.get('email'),
                user.get('name'),
                user.get('role', 'user'),
                json.dumps(user),
                user.get('created_at', datetime.utcnow().isoformat())
            ))
            
            self._connection.commit()
            return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute('SELECT data FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return json.loads(row['data']) if row else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute('SELECT data FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return json.loads(row['data']) if row else None
    
    def list_users(self, limit: int = 100) -> List[Dict]:
        """List all users"""
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute('SELECT data FROM users ORDER BY created_at DESC LIMIT ?', (limit,))
            return [json.loads(row['data']) for row in cursor.fetchall()]
    
    # Scan result operations
    def save_scan_result(self, scan_result: Dict) -> str:
        """Save a scan result"""
        with self._lock:
            cursor = self._connection.cursor()
            
            scan_id = scan_result.get('id') or self._generate_id('scan_')
            
            cursor.execute('''
                INSERT INTO scan_results 
                (id, account_id, regions, total_findings, critical_count, high_count, medium_count, low_count, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan_id,
                scan_result.get('account_id'),
                json.dumps(scan_result.get('regions', [])),
                scan_result.get('total_findings', 0),
                scan_result.get('critical_count', 0),
                scan_result.get('high_count', 0),
                scan_result.get('medium_count', 0),
                scan_result.get('low_count', 0),
                json.dumps(scan_result)
            ))
            
            self._connection.commit()
            return scan_id
    
    def get_scan_result(self, scan_id: str) -> Optional[Dict]:
        """Get scan result by ID"""
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute('SELECT data FROM scan_results WHERE id = ?', (scan_id,))
            row = cursor.fetchone()
            return json.loads(row['data']) if row else None
    
    def list_scan_results(self, account_id: str = None, limit: int = 100) -> List[Dict]:
        """List scan results"""
        with self._lock:
            cursor = self._connection.cursor()
            
            if account_id:
                cursor.execute(
                    'SELECT data FROM scan_results WHERE account_id = ? ORDER BY created_at DESC LIMIT ?',
                    (account_id, limit)
                )
            else:
                cursor.execute(
                    'SELECT data FROM scan_results ORDER BY created_at DESC LIMIT ?',
                    (limit,)
                )
            
            return [json.loads(row['data']) for row in cursor.fetchall()]


# ============================================================================
# IN-MEMORY ADAPTER (for testing)
# ============================================================================

class MemoryAdapter(DatabaseAdapter):
    """In-memory database adapter for testing"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config
        self._connected = False
        self._assessments = {}
        self._users = {}
        self._scan_results = {}
    
    def connect(self) -> bool:
        self._connected = True
        logger.info("Connected to in-memory database")
        return True
    
    def disconnect(self) -> None:
        self._connected = False
        logger.info("Disconnected from in-memory database")
    
    def is_connected(self) -> bool:
        return self._connected
    
    def _generate_id(self, prefix: str = '') -> str:
        import uuid
        return f"{prefix}{uuid.uuid4().hex[:16]}"
    
    def save_assessment(self, assessment: Dict) -> str:
        assessment_id = assessment.get('id') or self._generate_id('asmt_')
        assessment['id'] = assessment_id
        assessment['updated_at'] = datetime.utcnow().isoformat()
        self._assessments[assessment_id] = assessment
        return assessment_id
    
    def get_assessment(self, assessment_id: str) -> Optional[Dict]:
        return self._assessments.get(assessment_id)
    
    def list_assessments(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        assessments = list(self._assessments.values())
        if user_id:
            assessments = [a for a in assessments if a.get('user_id') == user_id]
        return sorted(assessments, key=lambda x: x.get('updated_at', ''), reverse=True)[:limit]
    
    def delete_assessment(self, assessment_id: str) -> bool:
        if assessment_id in self._assessments:
            del self._assessments[assessment_id]
            return True
        return False
    
    def save_user(self, user: Dict) -> str:
        user_id = user.get('id') or self._generate_id('user_')
        user['id'] = user_id
        self._users[user_id] = user
        return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        return self._users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        for user in self._users.values():
            if user.get('email') == email:
                return user
        return None
    
    def list_users(self, limit: int = 100) -> List[Dict]:
        return list(self._users.values())[:limit]
    
    def save_scan_result(self, scan_result: Dict) -> str:
        scan_id = scan_result.get('id') or self._generate_id('scan_')
        scan_result['id'] = scan_id
        scan_result['created_at'] = datetime.utcnow().isoformat()
        self._scan_results[scan_id] = scan_result
        return scan_id
    
    def get_scan_result(self, scan_id: str) -> Optional[Dict]:
        return self._scan_results.get(scan_id)
    
    def list_scan_results(self, account_id: str = None, limit: int = 100) -> List[Dict]:
        results = list(self._scan_results.values())
        if account_id:
            results = [r for r in results if r.get('account_id') == account_id]
        return sorted(results, key=lambda x: x.get('created_at', ''), reverse=True)[:limit]


# ============================================================================
# FIREBASE ADAPTER
# ============================================================================

class FirebaseAdapter(DatabaseAdapter):
    """Firebase Realtime Database adapter"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._db = None
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to Firebase"""
        try:
            import firebase_admin
            from firebase_admin import credentials, db
            
            if not firebase_admin._apps:
                if self.config.firebase_credentials:
                    cred = credentials.Certificate(self.config.firebase_credentials)
                else:
                    cred = credentials.ApplicationDefault()
                
                firebase_admin.initialize_app(cred, {
                    'databaseURL': self.config.firebase_url
                })
            
            self._db = db
            self._connected = True
            logger.info("Connected to Firebase Realtime Database")
            return True
            
        except ImportError:
            logger.error("firebase-admin package not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Firebase: {e}")
            return False
    
    def disconnect(self) -> None:
        self._connected = False
        logger.info("Disconnected from Firebase")
    
    def is_connected(self) -> bool:
        return self._connected
    
    def _generate_id(self, prefix: str = '') -> str:
        import uuid
        return f"{prefix}{uuid.uuid4().hex[:16]}"
    
    def save_assessment(self, assessment: Dict) -> str:
        assessment_id = assessment.get('id') or self._generate_id('asmt_')
        assessment['id'] = assessment_id
        assessment['updated_at'] = datetime.utcnow().isoformat()
        
        ref = self._db.reference(f'assessments/{assessment_id}')
        ref.set(assessment)
        return assessment_id
    
    def get_assessment(self, assessment_id: str) -> Optional[Dict]:
        ref = self._db.reference(f'assessments/{assessment_id}')
        return ref.get()
    
    def list_assessments(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        ref = self._db.reference('assessments')
        
        if user_id:
            query = ref.order_by_child('user_id').equal_to(user_id).limit_to_last(limit)
        else:
            query = ref.order_by_child('updated_at').limit_to_last(limit)
        
        data = query.get() or {}
        return list(data.values())
    
    def delete_assessment(self, assessment_id: str) -> bool:
        ref = self._db.reference(f'assessments/{assessment_id}')
        ref.delete()
        return True
    
    def save_user(self, user: Dict) -> str:
        user_id = user.get('id') or self._generate_id('user_')
        user['id'] = user_id
        
        ref = self._db.reference(f'users/{user_id}')
        ref.set(user)
        return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        ref = self._db.reference(f'users/{user_id}')
        return ref.get()
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        ref = self._db.reference('users')
        query = ref.order_by_child('email').equal_to(email).limit_to_first(1)
        data = query.get() or {}
        users = list(data.values())
        return users[0] if users else None
    
    def list_users(self, limit: int = 100) -> List[Dict]:
        ref = self._db.reference('users')
        data = ref.order_by_child('created_at').limit_to_last(limit).get() or {}
        return list(data.values())
    
    def save_scan_result(self, scan_result: Dict) -> str:
        scan_id = scan_result.get('id') or self._generate_id('scan_')
        scan_result['id'] = scan_id
        scan_result['created_at'] = datetime.utcnow().isoformat()
        
        ref = self._db.reference(f'scan_results/{scan_id}')
        ref.set(scan_result)
        return scan_id
    
    def get_scan_result(self, scan_id: str) -> Optional[Dict]:
        ref = self._db.reference(f'scan_results/{scan_id}')
        return ref.get()
    
    def list_scan_results(self, account_id: str = None, limit: int = 100) -> List[Dict]:
        ref = self._db.reference('scan_results')
        
        if account_id:
            query = ref.order_by_child('account_id').equal_to(account_id).limit_to_last(limit)
        else:
            query = ref.order_by_child('created_at').limit_to_last(limit)
        
        data = query.get() or {}
        return list(data.values())


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

_database_instance = None
_database_lock = threading.Lock()

def get_database(config: DatabaseConfig = None) -> DatabaseAdapter:
    """
    Get or create database instance (singleton pattern).
    
    Args:
        config: Database configuration (uses environment if None)
        
    Returns:
        DatabaseAdapter instance
    """
    global _database_instance
    
    with _database_lock:
        if _database_instance is not None:
            return _database_instance
        
        if config is None:
            config = DatabaseConfig.from_env()
        
        # Create adapter based on backend
        if config.backend == DatabaseBackend.FIREBASE:
            adapter = FirebaseAdapter(config)
        elif config.backend == DatabaseBackend.FIRESTORE:
            # Firestore adapter would be similar to Firebase
            adapter = FirebaseAdapter(config)  # Placeholder
        elif config.backend == DatabaseBackend.MEMORY:
            adapter = MemoryAdapter(config)
        else:
            adapter = SQLiteAdapter(config)
        
        # Connect
        if adapter.connect():
            _database_instance = adapter
            return adapter
        else:
            logger.error(f"Failed to connect to {config.backend.value} database")
            # Fallback to memory
            fallback = MemoryAdapter(config)
            fallback.connect()
            _database_instance = fallback
            return fallback


def reset_database():
    """Reset the database singleton (for testing)"""
    global _database_instance
    with _database_lock:
        if _database_instance:
            _database_instance.disconnect()
        _database_instance = None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'DatabaseBackend',
    'DatabaseConfig',
    'DatabaseAdapter',
    'SQLiteAdapter',
    'MemoryAdapter',
    'FirebaseAdapter',
    'get_database',
    'reset_database',
]
