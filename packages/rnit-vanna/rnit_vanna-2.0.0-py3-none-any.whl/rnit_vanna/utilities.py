"""
Utility classes for RNIT Vanna
Provides database inspection, training generation, and query optimization
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class DatabaseInspector:
    """
    Inspect database structure and generate training data
    """

    @staticmethod
    def inspect_sqlite(db_path: str) -> Dict[str, Any]:
        """
        Inspect SQLite database structure

        Args:
            db_path: Path to SQLite database

        Returns:
            Dictionary with database metadata
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        result = {
            'tables': {},
            'total_tables': 0,
            'total_columns': 0,
            'relationships': []
        }

        # Get all tables
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = cursor.fetchall()

        for table_name, ddl in tables:
            # Get columns for this table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            result['tables'][table_name] = {
                'ddl': ddl,
                'columns': [
                    {
                        'name': col[1],
                        'type': col[2],
                        'nullable': not col[3],
                        'primary_key': bool(col[5])
                    }
                    for col in columns
                ],
                'row_count': row_count,
                'foreign_keys': [
                    {
                        'column': fk[3],
                        'references_table': fk[2],
                        'references_column': fk[4]
                    }
                    for fk in foreign_keys
                ]
            }

            result['total_columns'] += len(columns)

            # Track relationships
            for fk in foreign_keys:
                result['relationships'].append({
                    'from_table': table_name,
                    'from_column': fk[3],
                    'to_table': fk[2],
                    'to_column': fk[4]
                })

        result['total_tables'] = len(tables)
        conn.close()

        return result

    @staticmethod
    def generate_summary(db_info: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of database structure

        Args:
            db_info: Database information from inspect_sqlite

        Returns:
            Formatted summary string
        """
        lines = [
            "DATABASE STRUCTURE SUMMARY",
            "=" * 50,
            f"Total Tables: {db_info['total_tables']}",
            f"Total Columns: {db_info['total_columns']}",
            f"Relationships: {len(db_info['relationships'])}",
            "",
            "TABLES:",
            "-" * 30
        ]

        for table_name, info in db_info['tables'].items():
            lines.append(f"\n{table_name}:")
            lines.append(f"  Rows: {info['row_count']:,}")
            lines.append(f"  Columns: {len(info['columns'])}")

            # Show columns
            for col in info['columns']:
                pk = " [PK]" if col['primary_key'] else ""
                null = "" if col['nullable'] else " NOT NULL"
                lines.append(f"    - {col['name']} ({col['type']}){null}{pk}")

            # Show foreign keys
            if info['foreign_keys']:
                lines.append("  Foreign Keys:")
                for fk in info['foreign_keys']:
                    lines.append(
                        f"    - {fk['column']} -> {fk['references_table']}.{fk['references_column']}"
                    )

        return "\n".join(lines)


class TrainingGenerator:
    """
    Generate training queries based on database structure
    """

    @staticmethod
    def generate_basic_queries(table_name: str, columns: List[Dict]) -> List[Dict]:
        """
        Generate basic training queries for a table

        Args:
            table_name: Name of the table
            columns: List of column information

        Returns:
            List of {question, sql} training pairs
        """
        queries = []

        # Select all
        queries.append({
            "question": f"Show all {table_name}",
            "sql": f"SELECT * FROM {table_name}"
        })

        queries.append({
            "question": f"Get all records from {table_name}",
            "sql": f"SELECT * FROM {table_name}"
        })

        # Count
        queries.append({
            "question": f"How many {table_name} are there?",
            "sql": f"SELECT COUNT(*) FROM {table_name}"
        })

        queries.append({
            "question": f"Count total {table_name}",
            "sql": f"SELECT COUNT(*) FROM {table_name}"
        })

        # Limit
        queries.append({
            "question": f"Show top 10 {table_name}",
            "sql": f"SELECT * FROM {table_name} LIMIT 10"
        })

        # For each column, generate specific queries
        for col in columns:
            col_name = col['name']
            col_type = col.get('type', 'TEXT')

            # Select specific column
            queries.append({
                "question": f"Show all {col_name} from {table_name}",
                "sql": f"SELECT {col_name} FROM {table_name}"
            })

            # Distinct values
            queries.append({
                "question": f"Show unique {col_name} from {table_name}",
                "sql": f"SELECT DISTINCT {col_name} FROM {table_name}"
            })

            # If numeric column, add aggregation queries
            if 'INT' in col_type.upper() or 'REAL' in col_type.upper() or 'NUMERIC' in col_type.upper():
                queries.append({
                    "question": f"What is the total {col_name} in {table_name}?",
                    "sql": f"SELECT SUM({col_name}) FROM {table_name}"
                })

                queries.append({
                    "question": f"What is the average {col_name} in {table_name}?",
                    "sql": f"SELECT AVG({col_name}) FROM {table_name}"
                })

                queries.append({
                    "question": f"What is the maximum {col_name} in {table_name}?",
                    "sql": f"SELECT MAX({col_name}) FROM {table_name}"
                })

        return queries

    @staticmethod
    def generate_join_queries(
        relationships: List[Dict],
        tables_info: Dict[str, Any]
    ) -> List[Dict]:
        """
        Generate JOIN queries based on foreign key relationships

        Args:
            relationships: List of foreign key relationships
            tables_info: Information about all tables

        Returns:
            List of {question, sql} training pairs
        """
        queries = []

        for rel in relationships:
            from_table = rel['from_table']
            to_table = rel['to_table']
            from_col = rel['from_column']
            to_col = rel['to_column']

            # Basic join
            queries.append({
                "question": f"Show {from_table} with their {to_table}",
                "sql": f"""SELECT * FROM {from_table}
                          JOIN {to_table} ON {from_table}.{from_col} = {to_table}.{to_col}"""
            })

            # Count join
            queries.append({
                "question": f"How many {from_table} per {to_table}?",
                "sql": f"""SELECT {to_table}.{to_col}, COUNT({from_table}.{from_col}) as count
                          FROM {to_table}
                          LEFT JOIN {from_table} ON {from_table}.{from_col} = {to_table}.{to_col}
                          GROUP BY {to_table}.{to_col}"""
            })

        return queries

    @staticmethod
    def save_training_queries(queries: List[Dict], filepath: str):
        """
        Save training queries to JSON file

        Args:
            queries: List of training queries
            filepath: Path to save JSON file
        """
        with open(filepath, 'w') as f:
            json.dump(queries, f, indent=2)
        print(f"Saved {len(queries)} training queries to {filepath}")


class QueryOptimizer:
    """
    Optimize and validate generated SQL queries
    """

    @staticmethod
    def validate_sql(sql: str, db_path: str) -> Dict[str, Any]:
        """
        Validate SQL query against database

        Args:
            sql: SQL query to validate
            db_path: Path to database

        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'error': None,
            'row_count': 0,
            'execution_plan': None
        }

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Try to execute the query
            cursor.execute(sql)
            rows = cursor.fetchall()
            result['valid'] = True
            result['row_count'] = len(rows)

            # Get execution plan
            cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
            result['execution_plan'] = cursor.fetchall()

            conn.close()

        except Exception as e:
            result['error'] = str(e)

        return result

    @staticmethod
    def suggest_indexes(db_info: Dict[str, Any]) -> List[str]:
        """
        Suggest indexes based on database structure

        Args:
            db_info: Database information from DatabaseInspector

        Returns:
            List of CREATE INDEX statements
        """
        suggestions = []

        for table_name, info in db_info['tables'].items():
            # Suggest indexes for foreign key columns
            for fk in info['foreign_keys']:
                index_name = f"idx_{table_name}_{fk['column']}"
                suggestions.append(
                    f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({fk['column']});"
                )

            # Suggest indexes for likely filter columns (name, email, date, etc.)
            for col in info['columns']:
                col_name = col['name'].lower()
                if any(keyword in col_name for keyword in ['name', 'email', 'date', 'status', 'type']):
                    if not col['primary_key']:  # Don't index primary keys (already indexed)
                        index_name = f"idx_{table_name}_{col['name']}"
                        suggestions.append(
                            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({col['name']});"
                        )

        return suggestions

    @staticmethod
    def format_sql(sql: str) -> str:
        """
        Format SQL query for better readability

        Args:
            sql: SQL query to format

        Returns:
            Formatted SQL query
        """
        # Simple formatting - can be enhanced
        keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN',
                   'INNER JOIN', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT']

        formatted = sql
        for keyword in keywords:
            formatted = formatted.replace(f' {keyword} ', f'\n{keyword} ')
            formatted = formatted.replace(f' {keyword.lower()} ', f'\n{keyword} ')

        # Clean up extra newlines
        lines = [line.strip() for line in formatted.split('\n') if line.strip()]
        return '\n'.join(lines)