"""
Enhanced Transaction Management for Database Operations
Fixes the psycopg2.errors.InFailedSqlTransaction error
"""
import logging
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import text

logger = logging.getLogger(__name__)

def safe_database_transaction(func):
    """
    Decorator to ensure safe transaction handling with proper rollback
    Fixes the InFailedSqlTransaction error by ensuring clean transaction state
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from core.app.extensions import db
        
        try:
            # Ensure clean transaction state before starting
            if db.session.in_transaction():
                db.session.rollback()
                logger.warning("Rolled back existing transaction before starting new operation")
            
            # Start fresh transaction
            result = func(*args, **kwargs)
            
            # Commit successful operation
            if db.session.in_transaction():
                db.session.commit()
                logger.debug("Database transaction committed successfully")
            
            return result
            
        except (IntegrityError, SQLAlchemyError) as db_error:
            # Always rollback on database errors
            try:
                if db.session.in_transaction():
                    db.session.rollback()
                    logger.error(f"Database error occurred, transaction rolled back: {str(db_error)}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {str(rollback_error)}")
            
            # Return structured error response
            return {
                'success': False,
                'message': 'Database error occurred while saving file record',
                'error': str(db_error),
                'error_type': 'database_error'
            }
            
        except Exception as e:
            # Rollback on any unexpected error
            try:
                if db.session.in_transaction():
                    db.session.rollback()
                    logger.error(f"Unexpected error occurred, transaction rolled back: {str(e)}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {str(rollback_error)}")
            
            # Return structured error response
            return {
                'success': False,
                'message': 'Unexpected error occurred during database operation',
                'error': str(e),
                'error_type': 'unexpected_error'
            }
    
    return wrapper

def reset_database_connection():
    """
    Reset database connection to clean state
    Ensures no pending transactions that could cause InFailedSqlTransaction
    """
    from core.app.extensions import db
    
    try:
        # Check if there's a pending transaction
        if db.session.in_transaction():
            db.session.rollback()
            logger.info("Rolled back pending transaction")
        
        # Test connection with simple query
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        
        logger.info("Database connection state reset successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset database connection: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass
        return False

def safe_file_record_creation(file_data):
    """
    Create file record with enhanced transaction safety
    """
    from core.app.extensions import db
    from app.models.temp import ResumeFile
    
    try:
        # Reset connection state first
        reset_database_connection()
        
        # Use explicit transaction block
        with db.session.begin():
            # Create the file record
            resume_file = ResumeFile(**file_data)
            db.session.add(resume_file)
            db.session.flush()  # Get ID but don't commit yet
            
            # Log successful creation
            logger.info(f"File record created with ID: {resume_file.id}")
            
            # Transaction will auto-commit at end of with block
            
        return {
            'success': True,
            'file_record': resume_file,
            'message': 'File record created successfully'
        }
        
    except IntegrityError as e:
        logger.error(f"Database integrity constraint violation: {str(e)}")
        
        # Handle specific constraint types
        error_message = "Database constraint violation"
        if "unique" in str(e).lower():
            error_message = "File with this name already exists"
        elif "foreign key" in str(e).lower():
            error_message = "Referenced record does not exist"
        
        return {
            'success': False,
            'message': error_message,
            'error': str(e),
            'error_type': 'integrity_error'
        }
        
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy database error: {str(e)}")
        return {
            'success': False,
            'message': 'Database error occurred while saving file record',
            'error': str(e),
            'error_type': 'sqlalchemy_error'
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in file record creation: {str(e)}")
        return {
            'success': False,
            'message': 'Unexpected error occurred during file creation',
            'error': str(e),
            'error_type': 'unexpected_error'
        }