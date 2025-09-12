"""
Pipeline Connector - A powerful Python package for connecting and orchestrating multiple data pipelines.

This package provides tools for:
- Connecting multiple pipelines seamlessly
- Managing data flow between pipelines
- Asynchronous pipeline execution
- Type-safe data validation
- Comprehensive error handling
"""

from .base import (
    BasePipeline, 
    PipelineError, 
    PipelineValidationError,
    PipelineExecutionError,
    PipelineConnectionError,
    PipelineConfig,
    PipelineStatus,
    PipelineMetrics
)
from .data_pipeline import (
    DataPipeline,
    DataSourcePipeline,
    DataSinkPipeline,
    BatchProcessingPipeline,
    AggregationPipeline
)
from .manager import PipelineManager
from .connectors import PipelineConnector, ConnectionType

__version__ = "0.1.0"
__author__ = "Krix Developer"
__email__ = "developer@example.com"

__all__ = [
    "BasePipeline",
    "DataPipeline",
    "DataSourcePipeline", 
    "DataSinkPipeline",
    "BatchProcessingPipeline",
    "AggregationPipeline",
    "PipelineManager",
    "PipelineConnector",
    "PipelineError",
    "PipelineValidationError",
    "PipelineExecutionError",
    "PipelineConnectionError",
    "PipelineConfig",
    "PipelineStatus",
    "PipelineMetrics",
    "ConnectionType",
]