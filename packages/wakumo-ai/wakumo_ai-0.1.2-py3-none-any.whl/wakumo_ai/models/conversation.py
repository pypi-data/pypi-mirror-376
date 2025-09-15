from pydantic import BaseModel
from typing import Optional

class ConversationCreateResponse(BaseModel):
    status: str
    conversation_id: str

class ConversationInfo(BaseModel):
    conversation_id: str
    title: str
    selected_repository: Optional[str]
    last_updated_at: Optional[str]
    created_at: Optional[str]
    agent_state: Optional[str]
    agent_states: Optional[dict]
    status: Optional[str]
