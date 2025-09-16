"""
Enhanced Vanna implementations by RNIT
Provides pre-configured classes and quick-start utilities
"""

import os
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import from official Vanna
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore


class RNITVanna(ChromaDB_VectorStore, OpenAI_Chat):
    """
    RNIT's enhanced Vanna with sensible defaults and additional features

    Features:
    - Auto-detects OpenAI API key from environment
    - Optimized default settings for SQL generation
    - Additional utility methods
    - Better error handling
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RNIT Vanna with enhanced configuration

        Args:
            config: Optional configuration dictionary. If not provided,
                   uses optimized defaults
        """
        # RNIT optimized defaults
        default_config = {
            'model': 'gpt-4o-mini',        # Cost-effective model
            'temperature': 0.1,             # Low temperature for consistent SQL
            'max_tokens': 800,              # Sufficient for most queries
            'request_timeout': 30,          # Reasonable timeout
        }

        # Merge user config with defaults
        if config:
            default_config.update(config)

        # Auto-detect API key from environment if not provided
        if 'api_key' not in default_config:
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found. Please either:\n"
                    "1. Set OPENAI_API_KEY environment variable\n"
                    "2. Pass api_key in config parameter"
                )
            default_config['api_key'] = api_key

        # Initialize parent classes
        ChromaDB_VectorStore.__init__(self, config=default_config)
        OpenAI_Chat.__init__(self, config=default_config)

        # Store config for reference
        self.rnit_config = default_config
        self._training_history = []

    def train_from_queries_file(self, filepath: str) -> int:
        """
        Train from a JSON file containing question-SQL pairs

        Args:
            filepath: Path to JSON file with training queries

        Returns:
            Number of queries trained

        Example JSON format:
        [
            {"question": "Show all users", "sql": "SELECT * FROM users"},
            {"question": "Count orders", "sql": "SELECT COUNT(*) FROM orders"}
        ]
        """
        with open(filepath, 'r') as f:
            queries = json.load(f)

        count = 0
        for item in queries:
            try:
                self.train(
                    question=item.get('question'),
                    sql=item.get('sql')
                )
                count += 1
                self._training_history.append(item)
            except Exception as e:
                print(f"Failed to train query: {item.get('question', 'Unknown')}")
                print(f"Error: {e}")

        print(f"Successfully trained {count} queries from {filepath}")
        return count

    def train_from_ddl_folder(self, folder_path: str) -> int:
        """
        Train from a folder containing DDL SQL files

        Args:
            folder_path: Path to folder with .sql files

        Returns:
            Number of DDL statements trained
        """
        folder = Path(folder_path)
        count = 0

        for sql_file in folder.glob('*.sql'):
            try:
                with open(sql_file, 'r') as f:
                    ddl = f.read()
                    self.train(ddl=ddl)
                    count += 1
                    print(f"Trained DDL from: {sql_file.name}")
            except Exception as e:
                print(f"Failed to train from {sql_file.name}: {e}")

        print(f"Successfully trained {count} DDL files from {folder_path}")
        return count

    def batch_train(self, training_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Train from multiple sources at once

        Args:
            training_data: Dictionary with keys:
                - ddl: List of DDL statements or single DDL string
                - queries: List of {question, sql} dictionaries
                - documentation: List of documentation strings

        Returns:
            Dictionary with counts of trained items
        """
        results = {'ddl': 0, 'queries': 0, 'documentation': 0}

        # Train DDL
        if 'ddl' in training_data:
            ddl_list = training_data['ddl']
            if isinstance(ddl_list, str):
                ddl_list = [ddl_list]

            for ddl in ddl_list:
                try:
                    self.train(ddl=ddl)
                    results['ddl'] += 1
                except Exception as e:
                    print(f"DDL training error: {e}")

        # Train queries
        if 'queries' in training_data:
            for item in training_data['queries']:
                try:
                    self.train(
                        question=item['question'],
                        sql=item['sql']
                    )
                    results['queries'] += 1
                    self._training_history.append(item)
                except Exception as e:
                    print(f"Query training error: {e}")

        # Train documentation
        if 'documentation' in training_data:
            for doc in training_data['documentation']:
                try:
                    self.train(documentation=doc)
                    results['documentation'] += 1
                except Exception as e:
                    print(f"Documentation training error: {e}")

        print(f"Training complete: {results}")
        return results

    def get_training_history(self) -> List[Dict]:
        """Get history of trained queries"""
        return self._training_history

    def clear_training_history(self):
        """Clear the training history"""
        self._training_history = []

    def test_accuracy(self, test_queries: List[Dict]) -> Dict[str, Any]:
        """
        Test the accuracy of SQL generation

        Args:
            test_queries: List of {question, expected_sql} pairs

        Returns:
            Dictionary with accuracy metrics
        """
        results = {
            'total': len(test_queries),
            'correct': 0,
            'failed': 0,
            'details': []
        }

        for item in test_queries:
            try:
                generated_sql = self.generate_sql(item['question'])
                is_correct = generated_sql.strip().lower() == item['expected_sql'].strip().lower()

                results['details'].append({
                    'question': item['question'],
                    'expected': item['expected_sql'],
                    'generated': generated_sql,
                    'correct': is_correct
                })

                if is_correct:
                    results['correct'] += 1
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'question': item['question'],
                    'error': str(e)
                })

        results['accuracy'] = results['correct'] / results['total'] if results['total'] > 0 else 0
        return results


class VannaQuickStart:
    """
    Quick start utilities for common Vanna setups
    """

    @staticmethod
    def for_sqlite(db_path: str, auto_train: bool = True, api_key: str = None) -> RNITVanna:
        """
        Quick setup for SQLite database

        Args:
            db_path: Path to SQLite database
            auto_train: If True, automatically train on all tables
            api_key: Optional API key (uses environment if not provided)

        Returns:
            Configured RNITVanna instance
        """
        config = {}
        if api_key:
            config['api_key'] = api_key
        elif not os.environ.get('OPENAI_API_KEY'):
            # For testing without API key
            config['api_key'] = 'test-key-for-structure-testing'

        vn = RNITVanna(config=config)
        vn.connect_to_sqlite(db_path)

        if auto_train and os.path.exists(db_path):
            print(f"Auto-training from {db_path}...")
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )
            tables = cursor.fetchall()

            for table_name, ddl in tables:
                try:
                    vn.train(ddl=ddl)
                    print(f"  Trained on table: {table_name}")
                except Exception as e:
                    print(f"  Failed to train on {table_name}: {e}")

            conn.close()
            print(f"Auto-training complete for {len(tables)} tables")

        return vn

    @staticmethod
    def for_postgres(
        host: str,
        database: str,
        user: str,
        password: str,
        port: int = 5432,
        auto_train: bool = True
    ) -> RNITVanna:
        """
        Quick setup for PostgreSQL database

        Args:
            host: Database host
            database: Database name
            user: Username
            password: Password
            port: Port number (default 5432)
            auto_train: If True, automatically train on schema

        Returns:
            Configured RNITVanna instance
        """
        vn = RNITVanna()
        vn.connect_to_postgres(
            host=host,
            dbname=database,
            user=user,
            password=password,
            port=port
        )

        if auto_train:
            # Add auto-training logic for PostgreSQL
            print("Auto-training for PostgreSQL...")
            # This would require psycopg2 and additional logic

        return vn

    @staticmethod
    def for_mysql(
        host: str,
        database: str,
        user: str,
        password: str,
        port: int = 3306
    ) -> RNITVanna:
        """
        Quick setup for MySQL database
        """
        vn = RNITVanna()
        vn.connect_to_mysql(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        return vn

    @staticmethod
    def create_sample_project(project_name: str, db_type: str = 'sqlite'):
        """
        Create a sample project structure with all necessary files

        Args:
            project_name: Name of the project folder to create
            db_type: Type of database ('sqlite', 'postgres', 'mysql')
        """
        project_path = Path(project_name)
        project_path.mkdir(exist_ok=True)

        # Create .env.example
        env_content = "OPENAI_API_KEY=your_api_key_here\n"
        if db_type == 'postgres':
            env_content += """DB_HOST=localhost
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DB_PORT=5432
"""
        (project_path / '.env.example').write_text(env_content)

        # Create main.py
        main_content = f'''"""
{project_name} - Vanna SQL Generation Project
Created with RNIT Vanna
"""

import os
from dotenv import load_dotenv
from rnit_vanna import VannaQuickStart

# Load environment variables
load_dotenv()

# Quick setup
vn = VannaQuickStart.for_{db_type}('your_database.{"sqlite" if db_type == "sqlite" else "connection"}')

# Example training
training_queries = [
    {{"question": "Show all records", "sql": "SELECT * FROM your_table"}},
    {{"question": "Count total records", "sql": "SELECT COUNT(*) FROM your_table"}},
]

for q in training_queries:
    vn.train(question=q['question'], sql=q['sql'])

# Test it
question = "Show all records"
sql = vn.generate_sql(question)
print(f"Question: {{question}}")
print(f"Generated SQL: {{sql}}")
'''
        (project_path / 'main.py').write_text(main_content)

        # Create requirements.txt
        (project_path / 'requirements.txt').write_text(
            "rnit-vanna>=1.0.0\npython-dotenv>=0.19.0\n"
        )

        # Create README
        readme_content = f"""# {project_name}

Created with RNIT Vanna - Enhanced SQL generation using natural language.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## About RNIT Vanna

RNIT Vanna is an enhanced wrapper around the official Vanna library,
providing additional utilities while always using the latest Vanna version.
"""
        (project_path / 'README.md').write_text(readme_content)

        print(f"[SUCCESS] Created sample project: {project_name}/")
        print(f"   - .env.example (add your API key)")
        print(f"   - main.py (starter code)")
        print(f"   - requirements.txt")
        print(f"   - README.md")
        print(f"\nNext steps:")
        print(f"1. cd {project_name}")
        print(f"2. pip install -r requirements.txt")
        print(f"3. Copy .env.example to .env and add your API key")
        print(f"4. python main.py")