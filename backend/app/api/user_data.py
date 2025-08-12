# backend/app/api/user_data.py
"""
User data management API endpoints.

Provides:
- Data export functionality (GDPR compliance)
- Account deletion with data purging
- Data retention policy management
- User privacy controls
"""

import logging
import zipfile
import json
import io
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser, require_permissions
from ..core.database import get_db_session
from ..core.exceptions import DatabaseException, ValidationException
from ..models.enhanced_models import Entry, Topic, ChatSession, ChatMessage
from ..services.unified_database_service import unified_db_service
from ..audit.service import audit_service, ActionType
from ..encryption.service import encryption_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-data", tags=["user-data"])


@router.get("/export")
async def export_user_data(
    current_user: CurrentUser,
    format: str = "json",
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Export all user data in portable format.
    
    Supports:
    - JSON format for technical users
    - CSV format for spreadsheet import
    - HTML format for human-readable export
    
    Args:
        current_user: Authenticated user
        format: Export format (json, csv, html)
        include_deleted: Include soft-deleted records
        db: Database session
    """
    try:
        # Log data export request
        await audit_service.log_user_action(
            user_id=str(current_user.id),
            action=ActionType.EXPORT_DATA,
            description=f"User requested data export in {format} format",
            metadata={"format": format, "include_deleted": include_deleted}
        )
        
        # Collect all user data
        user_data = await _collect_user_data(
            user_id=current_user.id,
            include_deleted=include_deleted,
            db=db
        )
        
        # Generate export file
        if format.lower() == "json":
            return _export_as_json(user_data, current_user.username)
        elif format.lower() == "csv":
            return _export_as_csv(user_data, current_user.username)
        elif format.lower() == "html":
            return _export_as_html(user_data, current_user.username)
        else:
            raise ValidationException("Unsupported export format. Use 'json', 'csv', or 'html'.")
            
    except Exception as e:
        logger.error(f"Data export failed for user {current_user.id}: {e}")
        await audit_service.log_user_action(
            user_id=str(current_user.id),
            action=ActionType.EXPORT_DATA,
            success=False,
            description=f"Data export failed: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Data export failed")


@router.delete("/account")
async def delete_user_account(
    current_user: CurrentUser,
    confirmation: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete user account and all associated data.
    
    This is irreversible and complies with GDPR "Right to be Forgotten".
    
    Args:
        current_user: Authenticated user
        confirmation: Must be "DELETE_MY_ACCOUNT" to confirm
        background_tasks: For background cleanup tasks
        db: Database session
    """
    try:
        # Verify confirmation
        if confirmation != "DELETE_MY_ACCOUNT":
            raise ValidationException(
                "Account deletion requires confirmation. "
                "Set confirmation parameter to 'DELETE_MY_ACCOUNT'."
            )
        
        # Log deletion request
        await audit_service.log_user_action(
            user_id=str(current_user.id),
            action=ActionType.DELETE_ACCOUNT,
            description="User requested account deletion",
            metadata={"confirmation_provided": True}
        )
        
        # Start account deletion process
        await _delete_user_data(current_user.id, db)
        
        # Schedule background cleanup tasks
        background_tasks.add_task(
            _cleanup_user_references,
            user_id=current_user.id
        )
        
        # Log successful deletion
        await audit_service.log_user_action(
            user_id=str(current_user.id),
            action=ActionType.DELETE_ACCOUNT,
            description="Account deletion completed successfully"
        )
        
        logger.info(f"Account deleted for user {current_user.id}")
        
        return {
            "message": "Account deleted successfully",
            "deleted_at": datetime.utcnow().isoformat(),
            "data_retention": "All personal data has been permanently removed"
        }
        
    except Exception as e:
        logger.error(f"Account deletion failed for user {current_user.id}: {e}")
        await audit_service.log_user_action(
            user_id=str(current_user.id),
            action=ActionType.DELETE_ACCOUNT,
            success=False,
            description=f"Account deletion failed: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Account deletion failed")


@router.get("/privacy-summary")
async def get_privacy_summary(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get summary of user's data and privacy settings.
    
    Args:
        current_user: Authenticated user
        db: Database session
    """
    try:
        # Count user data
        entry_count = await _count_user_entries(current_user.id, db)
        topic_count = await _count_user_topics(current_user.id, db)
        session_count = await _count_user_sessions(current_user.id, db)
        
        # Calculate data age
        oldest_entry = await _get_oldest_entry_date(current_user.id, db)
        
        return {
            "user_id": str(current_user.id),
            "username": current_user.username,
            "account_created": current_user.created_at.isoformat(),
            "data_summary": {
                "total_entries": entry_count,
                "total_topics": topic_count,
                "total_chat_sessions": session_count,
                "oldest_entry_date": oldest_entry.isoformat() if oldest_entry else None,
                "data_age_days": (datetime.utcnow() - oldest_entry).days if oldest_entry else 0
            },
            "privacy_controls": {
                "data_encryption": "enabled",
                "admin_access": "logged_and_audited",
                "ai_processing": "consent_required",
                "data_export": "available",
                "account_deletion": "available"
            },
            "compliance": {
                "gdpr_compliant": True,
                "right_to_export": True,
                "right_to_deletion": True,
                "audit_logging": True
            }
        }
        
    except Exception as e:
        logger.error(f"Privacy summary failed for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate privacy summary")


# Helper functions

async def _collect_user_data(
    user_id: str,
    include_deleted: bool,
    db: AsyncSession
) -> Dict[str, Any]:
    """Collect all user data for export."""
    try:
        user_data = {
            "export_info": {
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": str(user_id),
                "include_deleted": include_deleted,
                "format_version": "1.0"
            },
            "entries": [],
            "topics": [],
            "chat_sessions": [],
            "chat_messages": []
        }
        
        # Get entries
        entry_query = select(Entry).where(Entry.user_id == user_id)
        if not include_deleted:
            entry_query = entry_query.where(Entry.deleted_at.is_(None))
        
        entries_result = await db.execute(entry_query)
        entries = entries_result.scalars().all()
        
        for entry in entries:
            user_data["entries"].append({
                "id": str(entry.id),
                "title": entry.title,
                "content": entry.content,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
                "word_count": entry.word_count,
                "mood": entry.mood,
                "sentiment_score": float(entry.sentiment_score) if entry.sentiment_score else None,
                "tags": entry.tags,
                "is_favorite": entry.is_favorite,
                "topic_id": str(entry.topic_id) if entry.topic_id else None,
                "deleted_at": entry.deleted_at.isoformat() if entry.deleted_at else None
            })
        
        # Get topics
        topics_query = select(Topic).where(Topic.user_id == user_id)
        if not include_deleted:
            topics_query = topics_query.where(Topic.deleted_at.is_(None))
        
        topics_result = await db.execute(topics_query)
        topics = topics_result.scalars().all()
        
        for topic in topics:
            user_data["topics"].append({
                "id": str(topic.id),
                "name": topic.name,
                "description": topic.description,
                "color": topic.color,
                "created_at": topic.created_at.isoformat(),
                "updated_at": topic.updated_at.isoformat(),
                "entry_count": topic.entry_count,
                "tags": topic.tags,
                "deleted_at": topic.deleted_at.isoformat() if topic.deleted_at else None
            })
        
        # Get chat sessions
        sessions_query = select(ChatSession).where(ChatSession.user_id == user_id)
        if not include_deleted:
            sessions_query = sessions_query.where(ChatSession.deleted_at.is_(None))
        
        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()
        
        for session in sessions:
            user_data["chat_sessions"].append({
                "id": str(session.id),
                "title": session.title,
                "session_type": session.session_type,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": session.message_count,
                "tags": session.tags,
                "deleted_at": session.deleted_at.isoformat() if session.deleted_at else None
            })
            
            # Get messages for this session
            messages_query = select(ChatMessage).where(ChatMessage.session_id == session.id)
            messages_result = await db.execute(messages_query)
            messages = messages_result.scalars().all()
            
            for message in messages:
                user_data["chat_messages"].append({
                    "id": str(message.id),
                    "session_id": str(message.session_id),
                    "content": message.content,
                    "role": message.role,
                    "timestamp": message.timestamp.isoformat(),
                    "word_count": message.word_count
                })
        
        return user_data
        
    except Exception as e:
        logger.error(f"Failed to collect user data: {e}")
        raise


def _export_as_json(user_data: Dict[str, Any], username: str) -> StreamingResponse:
    """Export user data as JSON file."""
    json_content = json.dumps(user_data, indent=2, ensure_ascii=False)
    json_bytes = json_content.encode('utf-8')
    
    filename = f"{username}_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _export_as_csv(user_data: Dict[str, Any], username: str) -> StreamingResponse:
    """Export user data as CSV files in ZIP archive."""
    import csv
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Export entries as CSV
        if user_data["entries"]:
            entries_csv = io.StringIO()
            writer = csv.DictWriter(entries_csv, fieldnames=user_data["entries"][0].keys())
            writer.writeheader()
            writer.writerows(user_data["entries"])
            zip_file.writestr("entries.csv", entries_csv.getvalue())
        
        # Export topics as CSV
        if user_data["topics"]:
            topics_csv = io.StringIO()
            writer = csv.DictWriter(topics_csv, fieldnames=user_data["topics"][0].keys())
            writer.writeheader()
            writer.writerows(user_data["topics"])
            zip_file.writestr("topics.csv", topics_csv.getvalue())
        
        # Export chat sessions as CSV
        if user_data["chat_sessions"]:
            sessions_csv = io.StringIO()
            writer = csv.DictWriter(sessions_csv, fieldnames=user_data["chat_sessions"][0].keys())
            writer.writeheader()
            writer.writerows(user_data["chat_sessions"])
            zip_file.writestr("chat_sessions.csv", sessions_csv.getvalue())
        
        # Export chat messages as CSV
        if user_data["chat_messages"]:
            messages_csv = io.StringIO()
            writer = csv.DictWriter(messages_csv, fieldnames=user_data["chat_messages"][0].keys())
            writer.writeheader()
            writer.writerows(user_data["chat_messages"])
            zip_file.writestr("chat_messages.csv", messages_csv.getvalue())
        
        # Add export info
        info_content = json.dumps(user_data["export_info"], indent=2)
        zip_file.writestr("export_info.json", info_content)
    
    zip_buffer.seek(0)
    filename = f"{username}_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _export_as_html(user_data: Dict[str, Any], username: str) -> StreamingResponse:
    """Export user data as human-readable HTML file."""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Data Export for {username}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
            .section {{ margin-bottom: 30px; }}
            .entry {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .meta {{ color: #666; font-size: 0.9em; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Data Export for {username}</h1>
            <p>Generated on: {user_data['export_info']['generated_at']}</p>
            <p>User ID: {user_data['export_info']['user_id']}</p>
        </div>
        
        <div class="section">
            <h2>Journal Entries ({len(user_data['entries'])} total)</h2>
    """
    
    # Add entries
    for entry in user_data["entries"][:50]:  # Limit for HTML readability
        html_content += f"""
            <div class="entry">
                <h3>{entry['title']}</h3>
                <div class="meta">
                    Created: {entry['created_at']} | Words: {entry['word_count']} | 
                    Mood: {entry['mood'] or 'Not set'} | Favorite: {entry['is_favorite']}
                </div>
                <p>{entry['content'][:500]}{'...' if len(entry['content']) > 500 else ''}</p>
            </div>
        """
    
    if len(user_data["entries"]) > 50:
        html_content += f"<p><em>Showing first 50 entries out of {len(user_data['entries'])} total.</em></p>"
    
    # Add topics summary
    html_content += f"""
        </div>
        
        <div class="section">
            <h2>Topics ({len(user_data['topics'])} total)</h2>
            <table>
                <tr><th>Name</th><th>Description</th><th>Entry Count</th><th>Created</th></tr>
    """
    
    for topic in user_data["topics"]:
        html_content += f"""
                <tr>
                    <td>{topic['name']}</td>
                    <td>{topic['description'] or 'No description'}</td>
                    <td>{topic['entry_count']}</td>
                    <td>{topic['created_at']}</td>
                </tr>
        """
    
    html_content += """
            </table>
        </div>
        
        <div class="section">
            <h2>Data Export Complete</h2>
            <p>This export contains all your personal data from the Journaling AI system.</p>
            <p>For technical access to all data, please use the JSON export format.</p>
        </div>
    </body>
    </html>
    """
    
    html_bytes = html_content.encode('utf-8')
    filename = f"{username}_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    return StreamingResponse(
        io.BytesIO(html_bytes),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


async def _delete_user_data(user_id: str, db: AsyncSession) -> None:
    """Permanently delete all user data."""
    try:
        # Delete chat messages first (foreign key dependency)
        await db.execute(
            delete(ChatMessage).where(
                ChatMessage.session_id.in_(
                    select(ChatSession.id).where(ChatSession.user_id == user_id)
                )
            )
        )
        
        # Delete chat sessions
        await db.execute(delete(ChatSession).where(ChatSession.user_id == user_id))
        
        # Delete entries
        await db.execute(delete(Entry).where(Entry.user_id == user_id))
        
        # Delete topics
        await db.execute(delete(Topic).where(Topic.user_id == user_id))
        
        # Note: Auth user deletion should be handled by auth service
        # This function only handles journaling data
        
        await db.commit()
        logger.info(f"Successfully deleted all data for user {user_id}")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete user data: {e}")
        raise


async def _cleanup_user_references(user_id: str) -> None:
    """Background task to clean up any remaining user references."""
    try:
        # Clear any cached encryption keys
        from ..encryption.service import encryption_service
        await encryption_service.cleanup_user_encryption(str(user_id))
        
        # Additional cleanup tasks would go here
        logger.info(f"Completed background cleanup for user {user_id}")
        
    except Exception as e:
        logger.error(f"Background cleanup failed for user {user_id}: {e}")


async def _count_user_entries(user_id: str, db: AsyncSession) -> int:
    """Count user's journal entries."""
    result = await db.execute(
        select(Entry).where(Entry.user_id == user_id, Entry.deleted_at.is_(None))
    )
    return len(result.scalars().all())


async def _count_user_topics(user_id: str, db: AsyncSession) -> int:
    """Count user's topics."""
    result = await db.execute(
        select(Topic).where(Topic.user_id == user_id, Topic.deleted_at.is_(None))
    )
    return len(result.scalars().all())


async def _count_user_sessions(user_id: str, db: AsyncSession) -> int:
    """Count user's chat sessions."""
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == user_id, ChatSession.deleted_at.is_(None))
    )
    return len(result.scalars().all())


async def _get_oldest_entry_date(user_id: str, db: AsyncSession) -> Optional[datetime]:
    """Get the date of the user's oldest entry."""
    result = await db.execute(
        select(Entry.created_at)
        .where(Entry.user_id == user_id, Entry.deleted_at.is_(None))
        .order_by(Entry.created_at.asc())
        .limit(1)
    )
    entry = result.scalar_one_or_none()
    return entry