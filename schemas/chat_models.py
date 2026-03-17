from pydantic import BaseModel, Field, field_validator
from typing import Optional, List,Dict, Any,Annotated
from settings.app_config import DEFAULT_MODEL_ID


# For charts and session management
class S3Config(BaseModel):
    bucket_name: Annotated[str , Field(description="S3 Bucket Name is required")]
    region: Annotated[str,Field(description="S3 Bucket Region is required")]

# Mcp config
class MCPConfig(BaseModel):
    mcp_url:Annotated[str,Field(description="MCP URL is required")]
    mcp_type: Annotated[str , Field(description="Type of MCP server",examples=['streamable_http','sse','stdio'])]

# Agent config
class AgentConfig(BaseModel):
    model_id: Annotated[str,Field(default=DEFAULT_MODEL_ID, description="Model ID used by the agent")]
    instructions: Annotated[str, Field(description="Agent-specific instructions",default='you are helpful assistant')]
    temperature: Annotated[Optional[float],Field(default=None, ge=0, le=1.5, description="Temperature setting for the model")]
    top_p: Annotated[Optional[float],Field(default=None, ge=0,le=1.0, description="Top-p value for sampling")]
    max_tokens: Annotated[Optional[int], Field(default=None, description="Max tokens to generate (0 means no limit)")]
    thinking_max_tokens:Annotated[int,Field(default=8000, description="Max tokens for thinking step")]
    mcp_config: Annotated[Optional[List[MCPConfig]],Field(default_factory=list)]

    @field_validator("thinking_max_tokens")
    def cap_thinking_max_tokens(cls, v):
        if v > 10000:
            return 8000
        return v


class AgentConfigBlock(BaseModel):
    main: Annotated[AgentConfig, Field(description="Main agent configuration")]
    

# conversation manager
class S3ConversationManagerConfig(BaseModel):
    sliding_window_size: Optional[int] = Field(default=20,description="Maximum number of recent messages to keep")
    prefix: Optional[str] = Field(default="testing-default/", description="Optional key prefix for S3 objects")


# knowledge Base
class KnowledgeBaseDetail(BaseModel):
    id: str = Field(description="Unique ID of the knowledge base")
    description: str= Field(description="Detailed description of the knowledge base")

class ChatSessionRequest(BaseModel):
    """
    Canonical request payload for starting or continuing a chat session.
    """
    prompt: Annotated[str, Field(
        description="End‑user question or instruction",
        examples=['hi', 'hello', 'how can you help me today'],
    )]
    enable_thinking: Annotated[bool, Field(
        default=False,
        description="If true, stream intermediate reasoning tokens in addition to the final answer",
    )]
    session_id: Annotated[str, Field(
        description="Logical session/thread identifier; reuse to continue a conversation",
    )]
    visual_output: Annotated[bool, Field(
        default=False,
        description="Enable generation of matplotlib charts that are stored in S3",
    )]
    agent_config: Annotated[AgentConfigBlock, Field(
        description="Low‑level model/agent configuration forwarded to Bedrock",
    )]
    kb_details: Annotated[Optional[List[KnowledgeBaseDetail]], Field(
        default_factory=list,
        description="Optional list of knowledge base backends the agent can query",
    )]
    s3: Annotated[S3Config, Field(
        description="S3 configuration for both session history and visual assets",
    )]
    s3_conversation_config: Annotated[S3ConversationManagerConfig, Field(
        default_factory=S3ConversationManagerConfig,
        description="Sliding‑window configuration for the conversation history",
    )]
    agent_state: Annotated[Dict[str, Any], Field(
        default_factory=dict,
        description="Arbitrary key/value state passed through to tools and back to the client",
    )]
    enable_tools_reasoning: Annotated[bool, Field(
        default=True,
        description="If true and thinking is enabled, stream tool‑level reasoning messages",
    )]