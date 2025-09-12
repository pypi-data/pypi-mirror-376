"""
Base classes and core components for the pipeline connector package.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4


class PipelineError(Exception):
    """Base exception for pipeline-related errors."""
    
    def __init__(self, message: str, pipeline_id: Optional[str] = None, **kwargs):
        super().__init__(message)
        self.pipeline_id = pipeline_id
        self.details = kwargs


class PipelineValidationError(PipelineError):
    """Exception raised when pipeline data validation fails."""
    pass


class PipelineExecutionError(PipelineError):
    """Exception raised when pipeline execution fails."""
    pass


class PipelineConnectionError(PipelineError):
    """Exception raised when pipeline connection fails."""
    pass


class PipelineStatus(Enum):
    """Pipeline execution status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineConfig:
    """Configuration class for pipeline settings."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        batch_size: int = 100,
        timeout: float = 30.0,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        enable_logging: bool = True,
        log_level: str = "INFO",
        max_concurrent_tasks: int = 10
    ):
        """Initialize pipeline configuration."""
        self.name = name or f"pipeline_{uuid4().hex[:8]}"
        self.description = description
        self.batch_size = self._validate_positive_int(batch_size, "batch_size")
        self.timeout = self._validate_positive_float(timeout, "timeout")
        self.retry_attempts = self._validate_non_negative_int(retry_attempts, "retry_attempts")
        self.retry_delay = self._validate_non_negative_float(retry_delay, "retry_delay")
        self.enable_logging = enable_logging
        self.log_level = self._validate_log_level(log_level)
        self.max_concurrent_tasks = self._validate_positive_int(max_concurrent_tasks, "max_concurrent_tasks")
    
    def _validate_positive_int(self, value: int, field_name: str) -> int:
        """Validate that value is a positive integer."""
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer")
        return value
    
    def _validate_positive_float(self, value: float, field_name: str) -> float:
        """Validate that value is a positive float."""
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"{field_name} must be a positive number")
        return float(value)
    
    def _validate_non_negative_int(self, value: int, field_name: str) -> int:
        """Validate that value is a non-negative integer."""
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{field_name} must be a non-negative integer")
        return value
    
    def _validate_non_negative_float(self, value: float, field_name: str) -> float:
        """Validate that value is a non-negative float."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"{field_name} must be a non-negative number")
        return float(value)
    
    def _validate_log_level(self, value: str) -> str:
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        value_upper = value.upper()
        if value_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return value_upper
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'batch_size': self.batch_size,
            'timeout': self.timeout,
            'retry_attempts': self.retry_attempts,
            'retry_delay': self.retry_delay,
            'enable_logging': self.enable_logging,
            'log_level': self.log_level,
            'max_concurrent_tasks': self.max_concurrent_tasks
        }


class PipelineMetrics:
    """Metrics tracking for pipeline execution."""
    
    def __init__(
        self,
        pipeline_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        execution_time: Optional[float] = None,
        processed_items: int = 0,
        failed_items: int = 0,
        status: PipelineStatus = PipelineStatus.IDLE,
        error_message: Optional[str] = None
    ):
        """Initialize pipeline metrics."""
        self.pipeline_id = pipeline_id
        self.start_time = start_time
        self.end_time = end_time
        self.execution_time = execution_time
        self.processed_items = processed_items
        self.failed_items = failed_items
        self.status = status
        self.error_message = error_message
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'pipeline_id': self.pipeline_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'execution_time': self.execution_time,
            'processed_items': self.processed_items,
            'failed_items': self.failed_items,
            'status': self.status.value,
            'error_message': self.error_message
        }
    
    def copy(self) -> 'PipelineMetrics':
        """Create a copy of the metrics."""
        return PipelineMetrics(
            pipeline_id=self.pipeline_id,
            start_time=self.start_time,
            end_time=self.end_time,
            execution_time=self.execution_time,
            processed_items=self.processed_items,
            failed_items=self.failed_items,
            status=self.status,
            error_message=self.error_message
        )


class BasePipeline(ABC):
    """
    Abstract base class for all pipeline implementations.
    
    This class defines the interface that all pipelines must implement
    and provides common functionality for pipeline management.
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the pipeline with optional configuration.
        
        Args:
            config: Pipeline configuration object
        """
        self.config = config or PipelineConfig()
        self.id = uuid4().hex
        self.logger = self._setup_logger()
        self.metrics = PipelineMetrics(pipeline_id=self.id)
        self._connections: List['BasePipeline'] = []
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the pipeline."""
        logger = logging.getLogger(f"pipeline_connector.{self.config.name}")
        
        if self.config.enable_logging:
            logger.setLevel(getattr(logging, self.config.log_level))
            
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    async def process(self, data: Any) -> Any:
        """
        Process input data and return the result.
        
        This method must be implemented by all concrete pipeline classes.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
            
        Raises:
            PipelineExecutionError: If processing fails
        """
        pass
    
    async def validate_input(self, data: Any) -> bool:
        """
        Validate input data before processing.
        
        Args:
            data: Input data to validate
            
        Returns:
            True if data is valid
            
        Raises:
            PipelineValidationError: If validation fails
        """
        # Default implementation - can be overridden
        if data is None:
            raise PipelineValidationError("Input data cannot be None", self.id)
        return True
    
    async def validate_output(self, data: Any) -> bool:
        """
        Validate output data after processing.
        
        Args:
            data: Output data to validate
            
        Returns:
            True if data is valid
            
        Raises:
            PipelineValidationError: If validation fails
        """
        # Default implementation - can be overridden
        return True
    
    async def execute(self, data: Any, **kwargs) -> Any:
        """
        Execute the pipeline with input data.
        
        This method handles the full pipeline execution lifecycle including
        validation, processing, metrics tracking, and error handling.
        
        Args:
            data: Input data to process
            **kwargs: Additional execution parameters
            
        Returns:
            Processed data
            
        Raises:
            PipelineExecutionError: If execution fails
        """
        import time
        
        self.metrics.start_time = time.time()
        self.metrics.status = PipelineStatus.RUNNING
        
        try:
            self.logger.info(f"Starting pipeline execution: {self.config.name}")
            
            # Validate input
            await self.validate_input(data)
            
            # Process data with retry logic
            result = await self._execute_with_retry(data, **kwargs)
            
            # Validate output
            await self.validate_output(result)
            
            self.metrics.status = PipelineStatus.COMPLETED
            self.metrics.processed_items += 1
            
            self.logger.info(f"Pipeline execution completed: {self.config.name}")
            
            return result
            
        except Exception as e:
            self.metrics.status = PipelineStatus.FAILED
            self.metrics.failed_items += 1
            self.metrics.error_message = str(e)
            
            self.logger.error(f"Pipeline execution failed: {self.config.name} - {e}")
            
            if isinstance(e, (PipelineError, PipelineValidationError)):
                raise
            else:
                raise PipelineExecutionError(f"Execution failed: {e}", self.id) from e
                
        finally:
            self.metrics.end_time = time.time()
            if self.metrics.start_time:
                self.metrics.execution_time = self.metrics.end_time - self.metrics.start_time
    
    async def _execute_with_retry(self, data: Any, **kwargs) -> Any:
        """Execute with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.retry_attempts + 1):
            try:
                return await asyncio.wait_for(
                    self.process(data),
                    timeout=self.config.timeout
                )
            except Exception as e:
                last_exception = e
                
                if attempt < self.config.retry_attempts:
                    self.logger.warning(
                        f"Pipeline execution attempt {attempt + 1} failed, retrying in "
                        f"{self.config.retry_delay}s: {e}"
                    )
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    self.logger.error(f"All retry attempts exhausted: {e}")
        
        raise PipelineExecutionError(
            f"Failed after {self.config.retry_attempts + 1} attempts: {last_exception}",
            self.id
        ) from last_exception
    
    def add_connection(self, pipeline: 'BasePipeline') -> None:
        """Add a connection to another pipeline."""
        if pipeline not in self._connections:
            self._connections.append(pipeline)
    
    def remove_connection(self, pipeline: 'BasePipeline') -> None:
        """Remove a connection to another pipeline."""
        if pipeline in self._connections:
            self._connections.remove(pipeline)
    
    def get_connections(self) -> List['BasePipeline']:
        """Get all connected pipelines."""
        return self._connections.copy()
    
    def get_metrics(self) -> PipelineMetrics:
        """Get pipeline execution metrics."""
        return self.metrics.copy()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.config.name}')>"