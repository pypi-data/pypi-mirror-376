# portfolio.py

import json
from fastapi import HTTPException
from sqlalchemy import text
from typing import List, Dict, Any
from oak.main import get_db_session  # Import the shared context manager

def get_portfolio_holdings(user_id: str) -> List[Dict[str, Any]]:
    """
    Queries the database for all portfolio holdings associated with a given user ID.
    """
    try:
        with get_db_session() as conn:
            query = text("SELECT * FROM portfolio_holdings WHERE user_id = :user_id")
            result = conn.execute(query, {"user_id": user_id})
            holdings = [dict(row._mapping) for row in result.fetchall()]
        return holdings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

if __name__ == "__main__":
    try:
        user_id_to_query = "your_test_user_id"
        print(f"Querying portfolio holdings for user_id: {user_id_to_query}")
        portfolio_data = get_portfolio_holdings(user_id_to_query)
        print(json.dumps(portfolio_data, indent=2))
    except HTTPException as he:
        print(f"Error: {he.detail}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")