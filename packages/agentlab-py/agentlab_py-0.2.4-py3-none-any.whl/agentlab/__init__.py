"""AgentLab Python Client Library

A Python client library for the AgentLab evaluation platform using Connect RPC.
"""

from .client import AgentLabClient, AgentLabClientOptions, CreateEvaluationOptions
from .exceptions import AgentLabError, AuthenticationError, APIError

__version__ = "0.1.0"
__all__ = ["AgentLabClient", "AgentLabClientOptions", "CreateEvaluationOptions", "AgentLabError", "AuthenticationError", "APIError"]
