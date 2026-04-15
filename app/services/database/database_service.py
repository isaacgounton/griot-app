"""
Database service for job persistence and management.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import JobRecord, database_service
from app.models import Job, JobStatus
from loguru import logger

class DatabaseJobService:
    """Service for managing jobs in the database."""
    
    def _sanitize_for_json(self, data):
        """Recursively sanitize data for JSON serialization by converting Pydantic models to strings."""
        from pydantic import BaseModel
        
        if data is None:
            return None
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, dict):
            return {key: self._sanitize_for_json(value) for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_for_json(item) for item in data]
        elif isinstance(data, BaseModel):
            # Convert Pydantic models to dict, then recursively sanitize
            return self._sanitize_for_json(data.model_dump())
        else:
            # Convert any other object (like AnyUrl) to string
            try:
                return str(data)
            except:
                return None
    
    def _convert_datetime_to_naive(self, dt: datetime) -> datetime:
        """Convert timezone-aware datetime to naive datetime in UTC."""
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        if dt.tzinfo is not None:
            # Convert to UTC and remove timezone info
            utc_dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return utc_dt
        return dt
    
    async def save_job(self, job: Job) -> None:
        """Save or update a job in the database."""
        logger.info(f"Attempting to save job {job.id} to database with status {job.status}")
        async for session in database_service.get_session():
            logger.info(f"Got database session for job {job.id}")
            # Check if job exists
            result = await session.execute(
                select(JobRecord).where(JobRecord.id == job.id)
            )
            existing_job = result.scalar_one_or_none()

            if existing_job:
                logger.info(f"Updating existing job {job.id} - old status: {existing_job.status}, new status: {job.status}")
                # Update existing job - sanitize params and result for JSON serialization
                existing_job.operation = job.operation
                existing_job.params = self._sanitize_for_json(job.params)
                # Ensure we assign a JobStatus enum value
                if isinstance(job.status, str):
                    existing_job.status = JobStatus(job.status)
                else:
                    existing_job.status = job.status
                existing_job.result = self._sanitize_for_json(job.result)
                existing_job.error = job.error
                updated_at = datetime.fromisoformat(job.updated_at) if isinstance(job.updated_at, str) else job.updated_at
                existing_job.updated_at = self._convert_datetime_to_naive(updated_at)
            else:
                logger.info(f"Creating new job {job.id} with status {job.status}")
                # Create new job - sanitize params and result for JSON serialization
                job_record = JobRecord(
                    id=job.id,
                    operation=job.operation,
                    params=self._sanitize_for_json(job.params),
                    status=JobStatus(job.status) if isinstance(job.status, str) else job.status,
                    result=self._sanitize_for_json(job.result),
                    error=job.error,
                    created_at=self._convert_datetime_to_naive(datetime.fromisoformat(job.created_at) if isinstance(job.created_at, str) else job.created_at),
                    updated_at=self._convert_datetime_to_naive(datetime.fromisoformat(job.updated_at) if isinstance(job.updated_at, str) else job.updated_at)
                )
                session.add(job_record)

            await session.commit()
            logger.info(f"Committed job {job.id} to database with status {existing_job.status if existing_job else job.status}")
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID from the database."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(JobRecord).where(JobRecord.id == job_id)
            )
            job_record = result.scalar_one_or_none()
            
            if not job_record:
                return None
                
            return Job(
                id=job_record.id,
                operation=job_record.operation,
                params=job_record.params,
                status=job_record.status,
                result=job_record.result,
                error=job_record.error,
                created_at=job_record.created_at.isoformat(),
                updated_at=job_record.updated_at.isoformat()
            )
        
        return None  # Fallback return if session iteration fails
    
    async def get_all_jobs(self, limit: int = 100, offset: int = 0) -> List[Job]:
        """Get all jobs from the database, ordered by created_at descending."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(JobRecord)
                .order_by(JobRecord.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            job_records = result.scalars().all()
            
            jobs = []
            for job_record in job_records:
                # Handle enum conversion safely
                try:
                    if isinstance(job_record.status, str):
                        status = JobStatus(job_record.status.lower())
                    else:
                        status = job_record.status
                except (ValueError, AttributeError):
                    # Fallback to pending status if conversion fails
                    status = JobStatus.PENDING
                    
                job = Job(
                    id=job_record.id,
                    operation=job_record.operation,
                    params=job_record.params,
                    status=status,
                    result=job_record.result,
                    error=job_record.error,
                    created_at=job_record.created_at.isoformat(),
                    updated_at=job_record.updated_at.isoformat()
                )
                jobs.append(job)
            
            return jobs
        
        return []  # Fallback return
    
    async def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """Get all jobs with a specific status."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(JobRecord)
                .where(JobRecord.status == status)
                .order_by(JobRecord.created_at.desc())
            )
            job_records = result.scalars().all()
            
            jobs = []
            for job_record in job_records:
                # Handle enum conversion safely
                try:
                    if isinstance(job_record.status, str):
                        status = JobStatus(job_record.status.lower())
                    else:
                        status = job_record.status
                except (ValueError, AttributeError):
                    # Fallback to pending status if conversion fails
                    status = JobStatus.PENDING
                    
                job = Job(
                    id=job_record.id,
                    operation=job_record.operation,
                    params=job_record.params,
                    status=status,
                    result=job_record.result,
                    error=job_record.error,
                    created_at=job_record.created_at.isoformat(),
                    updated_at=job_record.updated_at.isoformat()
                )
                jobs.append(job)
            
            return jobs
        
        return []  # Fallback return
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job from the database."""
        async for session in database_service.get_session():
            try:
                result = await session.execute(
                    delete(JobRecord).where(JobRecord.id == job_id)
                )
                await session.commit()
                
                deleted = result.rowcount > 0
                logger.debug(f"Job {job_id} database deletion: {'success' if deleted else 'not found'}")
                return deleted
            except Exception as e:
                logger.error(f"Database error deleting job {job_id}: {e}")
                await session.rollback()
                raise
        
        logger.error(f"No database session available for deleting job {job_id}")
        return False  # Fallback return
    
    async def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed or failed jobs."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        cutoff_time = cutoff_time.replace(tzinfo=None)  # Convert to naive for database compatibility
        
        async for session in database_service.get_session():
            result = await session.execute(
                delete(JobRecord).where(
                    and_(
                        JobRecord.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]),
                        JobRecord.created_at < cutoff_time
                    )
                )
            )
            await session.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old jobs from database")
            return deleted_count
        
        return 0  # Fallback return
    
    async def get_job_count_by_status(self) -> dict[str, int]:
        """Get count of jobs by status."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(JobRecord.status, func.count(JobRecord.id))
                .group_by(JobRecord.status)
            )
            
            # Initialize with all statuses at 0
            counts = {status.value: 0 for status in JobStatus}
            
            for status, count in result:
                # Convert database enum string back to JobStatus enum
                try:
                    enum_status = JobStatus(status)
                    counts[enum_status.value] = count
                except ValueError:
                    # Handle any invalid status values gracefully
                    logger.warning(f"Unknown job status from database: {status}")
                    continue
                
            return counts
        
        # Fallback return with all statuses at 0
        return {status.value: 0 for status in JobStatus}
    
    async def get_video_creation_jobs_count(self, video_creation_types: set) -> int:
        """Get count of completed video creation jobs efficiently."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(func.count(JobRecord.id))
                .where(
                    and_(
                        JobRecord.operation.in_(video_creation_types),
                        JobRecord.status == JobStatus.COMPLETED
                    )
                )
            )
            count = result.scalar_one()
            return count
        
        return 0  # Fallback return

# Global database job service instance
db_job_service = DatabaseJobService()