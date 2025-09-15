import logging
import os
from contextlib import contextmanager

from sqlalchemy import text
import uvicorn
from fastapi import FastAPI, HTTPException
from oak.services.data_fetcher.database_service import get_db_connection
from oak.celery_app import celery_app
from oak.tasks.library import say_hello_task
from oak.config import Config

# Configure logging to display messages from the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI()

@contextmanager
def get_db_session():
    """
    Dependency to get a database connection that automatically closes.
    """
    conn = None
    try:
        conn = get_db_connection(db_uri=Config.SQLALCHEMY_DATABASE_URI)
        yield conn
    finally:
        if conn:
            conn.close()

@app.on_event("startup")
async def startup_event():
    """
    On application startup, check the database connection and
    ping the Celery worker to ensure all services are running.
    """
    logger.info("Starting up the application...")
    # Check database connection
    try:
        with get_db_session() as conn:
            # Execute a simple query to test the connection
            conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to the database.")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")

    # Check Celery worker connection
    try:
        # Ping the worker to check for a successful connection
        task_id = say_hello_task.delay("application startup").id
        logger.info(f"Sent a test task to Celery worker with ID: {task_id}")
    except Exception as e:
        logger.error(f"Failed to connect to Celery worker: {e}")

@app.get("/")
def read_root():
    """
    Root endpoint to verify the API is running.
    """
    return {"status": "ok", "message": "API is running and services are connected."}

@app.get("/get-tables")
def get_tables():
    """
    Endpoint to retrieve a list of all tables in the database.
    """
    try:
        with get_db_session() as conn:
            # Query the database for a list of all table names.
            # This query works for postgresql; adjust if using a different database.
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))

            tables = [row[0] for row in result.fetchall()]
        
        return {"status": "success", "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
