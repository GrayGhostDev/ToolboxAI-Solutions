"""
API endpoints for the prompt template organization system
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from core.prompts.integration import PromptTemplateIntegration
from core.prompts.models import (
    UserProfile, ContentRequirements, PersonalizationData,
    UniquenessEnhancement, ConversationStage, ContentType, GradeLevel,
    SubjectArea, LearningStyle, EngagementLevel, UniquenessFactor
)

logger = logging.getLogger(__name__)

# Initialize the prompt template integration
prompt_integration = PromptTemplateIntegration()

# Router setup
router = APIRouter(prefix="/prompt-templates", tags=["Prompt Templates"])

# Request/Response Models
class StartConversationRequest(BaseModel):
    user_id: str
    role: str
    experience_level: str = "beginner"
    interests: List[str] = Field(default_factory=list)
    cultural_background: Optional[str] = None
    initial_message: Optional[str] = None

class ProcessInputRequest(BaseModel):
    conversation_id: str
    user_input: str
    additional_context: Optional[Dict[str, Any]] = None

class PersonalizationRequest(BaseModel):
    conversation_id: str
    student_names: List[str] = Field(default_factory=list)
    local_landmarks: List[str] = Field(default_factory=list)
    cultural_elements: List[str] = Field(default_factory=list)
    school_theme: Optional[str] = None
    mascot: Optional[str] = None
    colors: List[str] = Field(default_factory=list)
    story_elements: List[str] = Field(default_factory=list)

class UniquenessRequest(BaseModel):
    conversation_id: str
    factors: List[str] = Field(default_factory=list)
    creative_twists: List[str] = Field(default_factory=list)
    personal_touches: List[str] = Field(default_factory=list)
    trending_elements: List[str] = Field(default_factory=list)

class ConversationResponse(BaseModel):
    conversation_id: str
    current_stage: str
    prompt_response: Dict[str, Any]
    flow_decision: str
    guidance: Dict[str, Any]
    validation: Dict[str, Any]
    next_steps: List[str]
    conversation_status: Dict[str, Any]

class ValidationResponse(BaseModel):
    is_valid: bool
    completeness_score: float
    uniqueness_score: float
    educational_value_score: float
    engagement_score: float
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    optimization_suggestions: List[str]
    quality_metrics: Dict[str, float]
    readiness_score: float

class WorkflowResponse(BaseModel):
    workflow_plan: Dict[str, Any]
    execution_results: Dict[str, Any]
    content_ready: bool

class AnalyticsResponse(BaseModel):
    conversation_id: str
    duration_minutes: float
    stages_completed: int
    current_stage: str
    data_points_collected: int
    quality_metrics: Dict[str, float]
    validation_summary: Dict[str, Any]
    readiness_score: float

# Helper function to get current user (mock for now)
def get_current_user():
    """Mock user for development"""
    class MockUser:
        def __init__(self):
            self.id = "dev-user-001"
            self.email = "teacher@example.com"
            self.role = "teacher"
            self.display_name = "Development Teacher"

    return MockUser()

@router.post("/conversations/start", response_model=ConversationResponse)
async def start_conversation(request: StartConversationRequest):
    """Start a new educational content creation conversation"""

    try:
        # Create user profile
        user_profile = UserProfile(
            user_id=request.user_id,
            role=request.role,
            experience_level=request.experience_level,
            interests=request.interests,
            cultural_background=request.cultural_background
        )

        # Start conversation
        context, prompt_response = await prompt_integration.start_educational_content_creation(
            user_profile, request.initial_message
        )

        # Get initial guidance
        guidance = await prompt_integration.guidance_system.provide_guidance(
            context, "suggestion", context.current_stage.value
        )

        # Get validation
        validation = await prompt_integration.validation_system.validate_conversation_context(context)

        # Get next steps
        next_steps = await prompt_integration.guidance_system.get_next_steps(context)

        # Get conversation status
        conversation_status = await prompt_integration.flow_manager.get_conversation_status(context.conversation_id)

        return ConversationResponse(
            conversation_id=context.conversation_id,
            current_stage=context.current_stage.value,
            prompt_response=prompt_response.dict(),
            flow_decision="continue",
            guidance=guidance,
            validation=validation.dict(),
            next_steps=next_steps,
            conversation_status=conversation_status
        )

    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}"
        )

@router.post("/conversations/process", response_model=ConversationResponse)
async def process_user_input(request: ProcessInputRequest):
    """Process user input in an existing conversation"""

    try:
        # Process input
        prompt_response, flow_decision, response_metadata = await prompt_integration.process_user_input(
            request.conversation_id, request.user_input, request.additional_context
        )

        return ConversationResponse(
            conversation_id=request.conversation_id,
            current_stage=prompt_response.template_id,  # This would be the actual stage
            prompt_response=prompt_response.dict(),
            flow_decision=flow_decision.value,
            guidance=response_metadata["guidance"],
            validation=response_metadata["validation"],
            next_steps=response_metadata["next_steps"],
            conversation_status=response_metadata["conversation_status"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to process user input: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process user input: {str(e)}"
        )

@router.post("/conversations/{conversation_id}/personalize")
async def personalize_content(conversation_id: str, request: PersonalizationRequest):
    """Add personalization data to a conversation"""

    try:
        # Create personalization data
        personalization_data = PersonalizationData(
            student_names=request.student_names,
            local_landmarks=request.local_landmarks,
            cultural_elements=request.cultural_elements,
            school_theme=request.school_theme,
            mascot=request.mascot,
            colors=request.colors,
            story_elements=request.story_elements
        )

        # Apply personalization
        result = await prompt_integration.personalize_content(conversation_id, personalization_data)

        return {
            "success": True,
            "message": "Personalization data added successfully",
            "personalized_prompt": result["personalized_prompt"],
            "personalization_score": result["personalization_score"],
            "suggestions": result["suggestions"]
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to personalize content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to personalize content: {str(e)}"
        )

@router.post("/conversations/{conversation_id}/enhance-uniqueness")
async def enhance_uniqueness(conversation_id: str, request: UniquenessRequest):
    """Enhance content uniqueness"""

    try:
        # Apply uniqueness enhancement
        result = await prompt_integration.enhance_content_uniqueness(
            conversation_id, request.factors, request.creative_twists
        )

        return {
            "success": True,
            "message": "Uniqueness enhancement applied successfully",
            "enhanced_prompt": result["enhanced_prompt"],
            "uniqueness_score": result["uniqueness_score"],
            "suggestions": result["suggestions"]
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to enhance uniqueness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enhance uniqueness: {str(e)}"
        )

@router.get("/conversations/{conversation_id}/validate", response_model=ValidationResponse)
async def validate_conversation(conversation_id: str):
    """Validate and optimize a conversation"""

    try:
        # Get validation and optimization
        result = await prompt_integration.validate_and_optimize(conversation_id)

        return ValidationResponse(
            is_valid=result["validation_result"]["is_valid"],
            completeness_score=result["validation_result"]["completeness_score"],
            uniqueness_score=result["validation_result"]["uniqueness_score"],
            educational_value_score=result["validation_result"]["educational_value_score"],
            engagement_score=result["validation_result"]["engagement_score"],
            errors=result["validation_result"]["errors"],
            warnings=result["validation_result"]["warnings"],
            suggestions=result["validation_result"]["suggestions"],
            optimization_suggestions=result["optimization_suggestions"],
            quality_metrics=result["quality_metrics"],
            readiness_score=result["readiness_score"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to validate conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate conversation: {str(e)}"
        )

@router.post("/conversations/{conversation_id}/generate-workflow", response_model=WorkflowResponse)
async def generate_workflow(conversation_id: str, background_tasks: BackgroundTasks):
    """Generate content creation workflow"""

    try:
        # Generate workflow
        result = await prompt_integration.generate_content_workflow(conversation_id)

        return WorkflowResponse(
            workflow_plan=result["workflow_plan"],
            execution_results=result["execution_results"],
            content_ready=result["content_ready"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to generate workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate workflow: {str(e)}"
        )

@router.get("/conversations/{conversation_id}/analytics", response_model=AnalyticsResponse)
async def get_conversation_analytics(conversation_id: str):
    """Get analytics for a conversation"""

    try:
        # Get analytics
        analytics = await prompt_integration.get_conversation_analytics(conversation_id)

        return AnalyticsResponse(**analytics)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )

@router.get("/conversations")
async def list_conversations():
    """List all active conversations"""

    try:
        conversations = prompt_integration.get_active_conversations()

        return {
            "conversations": conversations,
            "count": len(conversations)
        }

    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )

@router.delete("/conversations/{conversation_id}")
async def cleanup_conversation(conversation_id: str):
    """Clean up a completed conversation"""

    try:
        success = await prompt_integration.cleanup_conversation(conversation_id)

        if success:
            return {"success": True, "message": "Conversation cleaned up successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

    except Exception as e:
        logger.error(f"Failed to cleanup conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup conversation: {str(e)}"
        )

@router.get("/system/status")
async def get_system_status():
    """Get system status"""

    try:
        status = await prompt_integration.get_system_status()
        return status

    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )

@router.get("/templates")
async def list_templates():
    """List all available prompt templates"""

    try:
        templates = prompt_integration.template_engine.get_all_templates()

        return {
            "templates": [
                {
                    "id": template.id,
                    "name": template.name,
                    "stage": template.stage.value,
                    "content_type": template.content_type.value if template.content_type else None,
                    "priority": template.priority,
                    "is_active": template.is_active
                }
                for template in templates
            ],
            "count": len(templates)
        }

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )

@router.get("/guidance/{stage}")
async def get_guidance(stage: str):
    """Get guidance for a specific conversation stage"""

    try:
        # Convert string to ConversationStage enum
        try:
            conversation_stage = ConversationStage(stage)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stage: {stage}"
            )

        # Get guidance
        guidance = await prompt_integration.guidance_system.provide_guidance(
            None, "suggestion", stage
        )

        return guidance

    except Exception as e:
        logger.error(f"Failed to get guidance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get guidance: {str(e)}"
        )









