from pydantic import BaseModel, Field
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class AgentConfig(BaseModel):
    """Configuration cho Research Agent"""

    #API Keys
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    serper_api_key: str = Field(default_factory=lambda: os.getenv("SERPER_API_KEY"))
    
    # Model settings
    model_name: str = "gpt-4-turbo-preview"
    temperature: float = 0.1
    max_tokens: int = 4000

    # agent settings
    max_iterations: int = 5
    max_execution_time: int = 300

    # Memory settings
    memory_window: int = 10
    enable_long_term_memory: bool = True

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0

    # Search Setting
    max_search_results: int = 5
    search_timeout: int = 30

    # Parallel execution
    max_concurrent_tasks: int = 3

    class Config:
        arbitrary_types_allowed = True

# Global Config relases
config = AgentConfig()
    