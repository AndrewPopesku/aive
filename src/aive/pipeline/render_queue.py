"""
RenderQueue class with sequential and parallel processing capabilities.
"""
import multiprocessing as mp
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime

from ..core.timeline import Timeline
from ..ports.renderer import Renderer, RenderOptions, RenderError
from ..templates.placeholder import VideoTemplate


class JobStatus(Enum):
    """Status of a render job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueMode(Enum):
    """Processing mode for the render queue."""
    SEQUENTIAL = "sequential"
    PARALLEL_PROCESS = "parallel_process"
    PARALLEL_THREAD = "parallel_thread"


@dataclass
class RenderJob:
    """Represents a single render job in the queue."""
    id: str
    timeline: Timeline
    output_path: Path
    renderer: Renderer
    options: Optional[RenderOptions] = None
    template_data: Optional[Dict[str, Any]] = None  # For template-based jobs
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0  # 0.0 to 100.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Get the job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_finished(self) -> bool:
        """Check if the job is finished (completed, failed, or cancelled)."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary representation."""
        return {
            'id': self.id,
            'output_path': str(self.output_path),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'progress': self.progress,
            'error_message': self.error_message,
            'metadata': self.metadata,
        }


class JobProgressCallback:
    """Callback interface for job progress updates."""
    
    def __init__(self, callback: Optional[Callable[[RenderJob], None]] = None):
        self.callback = callback
    
    def on_job_started(self, job: RenderJob) -> None:
        """Called when a job starts."""
        if self.callback:
            self.callback(job)
    
    def on_job_progress(self, job: RenderJob, progress: float) -> None:
        """Called when job progress updates."""
        job.progress = progress
        if self.callback:
            self.callback(job)
    
    def on_job_completed(self, job: RenderJob) -> None:
        """Called when a job completes successfully."""
        if self.callback:
            self.callback(job)
    
    def on_job_failed(self, job: RenderJob, error: Exception) -> None:
        """Called when a job fails."""
        job.error_message = str(error)
        if self.callback:
            self.callback(job)


def _render_job_worker(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker function for multiprocessing render jobs.
    
    This function is defined at module level to be picklable.
    """
    try:
        # Reconstruct job from serialized data
        # Note: In a real implementation, this would need proper serialization
        # of Timeline and Renderer objects, which is complex
        
        result = {
            'job_id': job_data['job_id'],
            'status': 'completed',
            'error': None,
            'started_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
        }
        
        # Simulate rendering work
        time.sleep(1)  # Placeholder for actual rendering
        
        return result
        
    except Exception as e:
        return {
            'job_id': job_data['job_id'],
            'status': 'failed',
            'error': str(e),
            'started_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
        }


class RenderQueue:
    """
    A queue for managing and processing video render jobs.
    
    Supports both sequential and parallel processing with progress tracking
    and error handling.
    """
    
    def __init__(
        self,
        default_renderer: Optional[Renderer] = None,
        progress_callback: Optional[Callable[[RenderJob], None]] = None,
    ):
        """
        Initialize the render queue.
        
        Args:
            default_renderer: Default renderer to use for jobs without one
            progress_callback: Callback function for job progress updates
        """
        self.default_renderer = default_renderer
        self.progress_callback = JobProgressCallback(progress_callback)
        
        self._jobs: Dict[str, RenderJob] = {}
        self._job_order: List[str] = []  # Maintain insertion order
        self._running = False
        self._cancelled = False
        
        # Threading
        self._lock = threading.Lock()
        self._executor: Optional[Union[ProcessPoolExecutor, ThreadPoolExecutor]] = None
    
    def add_job(
        self,
        timeline: Timeline,
        output_path: Union[str, Path],
        renderer: Optional[Renderer] = None,
        options: Optional[RenderOptions] = None,
        job_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a render job to the queue.
        
        Args:
            timeline: Timeline to render
            output_path: Path where the video should be saved
            renderer: Renderer to use (uses default if None)
            options: Rendering options
            job_id: Custom job ID (generates UUID if None)
            metadata: Additional metadata for the job
            
        Returns:
            Job ID
            
        Raises:
            ValueError: If no renderer is available
        """
        if renderer is None:
            renderer = self.default_renderer
        
        if renderer is None:
            raise ValueError("No renderer provided and no default renderer set")
        
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        job = RenderJob(
            id=job_id,
            timeline=timeline,
            output_path=Path(output_path),
            renderer=renderer,
            options=options,
            metadata=metadata or {},
        )
        
        with self._lock:
            self._jobs[job_id] = job
            self._job_order.append(job_id)
        
        return job_id
    
    def add_template_job(
        self,
        template: VideoTemplate,
        data: Dict[str, Any],
        output_path: Union[str, Path],
        renderer: Optional[Renderer] = None,
        options: Optional[RenderOptions] = None,
        job_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a template-based render job to the queue.
        
        Args:
            template: Video template to fill and render
            data: Data to fill the template with
            output_path: Path where the video should be saved
            renderer: Renderer to use
            options: Rendering options
            job_id: Custom job ID
            metadata: Additional metadata
            
        Returns:
            Job ID
        """
        # Fill the template to create a timeline
        timeline = template.fill(data)
        
        if metadata is None:
            metadata = {}
        metadata['template_name'] = template.info.name
        metadata['template_data'] = data
        
        return self.add_job(
            timeline=timeline,
            output_path=output_path,
            renderer=renderer,
            options=options,
            job_id=job_id,
            metadata=metadata,
        )
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the queue.
        
        Args:
            job_id: ID of the job to remove
            
        Returns:
            True if job was removed, False if not found
        """
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                if job.status == JobStatus.RUNNING:
                    job.status = JobStatus.CANCELLED
                
                del self._jobs[job_id]
                if job_id in self._job_order:
                    self._job_order.remove(job_id)
                return True
        return False
    
    def get_job(self, job_id: str) -> Optional[RenderJob]:
        """Get a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def list_jobs(self, status: Optional[JobStatus] = None) -> List[RenderJob]:
        """
        List all jobs, optionally filtered by status.
        
        Args:
            status: Filter by job status
            
        Returns:
            List of jobs
        """
        with self._lock:
            jobs = [self._jobs[job_id] for job_id in self._job_order if job_id in self._jobs]
            
            if status is not None:
                jobs = [job for job in jobs if job.status == status]
            
            return jobs
    
    def clear_completed(self) -> int:
        """
        Remove all completed/failed/cancelled jobs from the queue.
        
        Returns:
            Number of jobs removed
        """
        removed_count = 0
        with self._lock:
            jobs_to_remove = []
            for job_id, job in self._jobs.items():
                if job.is_finished:
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self._jobs[job_id]
                if job_id in self._job_order:
                    self._job_order.remove(job_id)
                removed_count += 1
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            jobs = list(self._jobs.values())
            
            stats = {
                'total_jobs': len(jobs),
                'pending': sum(1 for j in jobs if j.status == JobStatus.PENDING),
                'running': sum(1 for j in jobs if j.status == JobStatus.RUNNING),
                'completed': sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
                'failed': sum(1 for j in jobs if j.status == JobStatus.FAILED),
                'cancelled': sum(1 for j in jobs if j.status == JobStatus.CANCELLED),
                'queue_running': self._running,
            }
            
            # Calculate average duration for completed jobs
            completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED and j.duration]
            if completed_jobs:
                stats['avg_duration'] = sum(j.duration for j in completed_jobs) / len(completed_jobs)
            else:
                stats['avg_duration'] = None
            
            return stats
    
    def run(self, mode: QueueMode = QueueMode.SEQUENTIAL, workers: int = None) -> None:
        """
        Process all jobs in the queue.
        
        Args:
            mode: Processing mode (sequential or parallel)
            workers: Number of worker processes/threads (auto-detected if None)
        """
        if self._running:
            raise RuntimeError("Queue is already running")
        
        self._running = True
        self._cancelled = False
        
        try:
            if mode == QueueMode.SEQUENTIAL:
                self._run_sequential()
            elif mode == QueueMode.PARALLEL_PROCESS:
                self._run_parallel_process(workers)
            elif mode == QueueMode.PARALLEL_THREAD:
                self._run_parallel_thread(workers)
            else:
                raise ValueError(f"Unsupported queue mode: {mode}")
        finally:
            self._running = False
            if self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None
    
    def stop(self) -> None:
        """Stop processing jobs."""
        self._cancelled = True
        if self._executor:
            self._executor.shutdown(wait=False)
    
    def _run_sequential(self) -> None:
        """Run jobs sequentially in the current thread."""
        while not self._cancelled:
            job = self._get_next_pending_job()
            if job is None:
                break  # No more pending jobs
            
            self._process_job(job)
    
    def _run_parallel_process(self, workers: Optional[int] = None) -> None:
        """Run jobs in parallel using multiprocessing."""
        if workers is None:
            workers = mp.cpu_count()
        
        # Note: This is a simplified implementation
        # In practice, multiprocessing with Timeline objects is complex
        # due to serialization requirements
        
        print(f"Warning: Multiprocessing mode is not fully implemented.")
        print("Falling back to sequential processing.")
        self._run_sequential()
    
    def _run_parallel_thread(self, workers: Optional[int] = None) -> None:
        """Run jobs in parallel using threading."""
        if workers is None:
            workers = min(4, mp.cpu_count())  # Conservative default for threading
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            self._executor = executor
            futures = {}
            
            while not self._cancelled:
                # Submit new jobs
                pending_jobs = self.list_jobs(JobStatus.PENDING)
                running_jobs = self.list_jobs(JobStatus.RUNNING)
                
                # Don't exceed worker limit
                available_slots = workers - len(running_jobs)
                jobs_to_submit = pending_jobs[:available_slots]
                
                for job in jobs_to_submit:
                    future = executor.submit(self._process_job, job)
                    futures[future] = job
                
                if not futures and not running_jobs:
                    break  # No more jobs to process
                
                # Wait for some jobs to complete
                if futures:
                    for future in as_completed(futures, timeout=1.0):
                        completed_job = futures.pop(future)
                        try:
                            future.result()  # Get result or raise exception
                        except Exception as e:
                            self._handle_job_error(completed_job, e)
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
    
    def _get_next_pending_job(self) -> Optional[RenderJob]:
        """Get the next pending job from the queue."""
        with self._lock:
            for job_id in self._job_order:
                if job_id in self._jobs:
                    job = self._jobs[job_id]
                    if job.status == JobStatus.PENDING:
                        return job
        return None
    
    def _process_job(self, job: RenderJob) -> None:
        """Process a single render job."""
        try:
            # Mark job as running
            with self._lock:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now()
            
            self.progress_callback.on_job_started(job)
            
            # Perform the actual rendering
            job.renderer.render(job.timeline, job.output_path, job.options)
            
            # Mark job as completed
            with self._lock:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.progress = 100.0
            
            self.progress_callback.on_job_completed(job)
            
        except Exception as e:
            self._handle_job_error(job, e)
    
    def _handle_job_error(self, job: RenderJob, error: Exception) -> None:
        """Handle job error."""
        with self._lock:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            job.error_message = str(error)
        
        self.progress_callback.on_job_failed(job, error)
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all jobs to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all jobs completed, False if timeout reached
        """
        start_time = time.time()
        
        while self._running:
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            pending_or_running = len([
                j for j in self._jobs.values() 
                if j.status in [JobStatus.PENDING, JobStatus.RUNNING]
            ])
            
            if pending_or_running == 0:
                return True
            
            time.sleep(0.1)
        
        return True
    
    def __len__(self) -> int:
        """Return the number of jobs in the queue."""
        return len(self._jobs)
    
    def __bool__(self) -> bool:
        """Return True if the queue has jobs."""
        return len(self._jobs) > 0
