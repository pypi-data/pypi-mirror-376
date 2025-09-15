# goals.py

import json
from fastapi import HTTPException
from sqlalchemy import text
from typing import List, Dict, Any
from oak.main import get_db_session

def get_user_goals(user_id: str) -> List[Dict[str, Any]]:
    """
    Queries the database for all goals associated with a given user ID.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A list of dictionaries, where each dictionary represents a user goal.

    Raises:
        HTTPException: If the database query fails.
    """
    try:
        with get_db_session() as conn:
            query = text("SELECT * FROM user_goal WHERE user_id = :user_id")
            result = conn.execute(query, {"user_id": user_id})
            goals = [dict(row._mapping) for row in result.fetchall()]
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

if __name__ == "__main__":
    # Example usage for demonstration purposes
    try:
        user_id_to_query = "your_test_user_id"  # Replace with a valid user ID
        print(f"Querying goals for user_id: {user_id_to_query}")
        goals_data = get_user_goals(user_id_to_query)
        print(json.dumps(goals_data, indent=2))
    except HTTPException as he:
        print(f"Error: {he.detail}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")