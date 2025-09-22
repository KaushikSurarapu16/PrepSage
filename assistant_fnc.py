from livekit.agents import llm
from typing import Annotated
import logging

logger = logging.getLogger("assistant-fnc")
logger.setLevel(logging.INFO)

class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()
        # Example internal state for user profile or context
        self._user_profile = {
            "name": "",
            "school": "",
            "interview_status": ""
        }
    
    def get_profile_str(self) -> str:
        profile_str = ""
        for key, value in self._user_profile.items():
            profile_str += f"{key.capitalize()}: {value}\n"
        return profile_str
    
    @llm.ai_callable(description="Set user profile information")
    def set_profile(
        self,
        name: Annotated[str, llm.TypeInfo(description="User's name")],
        school: Annotated[str, llm.TypeInfo(description="User's school name")],
        interview_status: Annotated[str, llm.TypeInfo(description="Interview status or notes")]
    ):
        logger.info("Setting profile: name=%s, school=%s, interview_status=%s", name, school, interview_status)
        self._user_profile.update({
            "name": name,
            "school": school,
            "interview_status": interview_status
        })
        return "User profile updated."
    
    @llm.ai_callable(description="Get the current user profile details")
    def get_profile(self):
        logger.info("Getting user profile")
        return self.get_profile_str()
    
    @llm.ai_callable(description="Provide interview tips")
    def interview_tips(self):
        logger.info("Providing interview tips")
        return (
            "Here are some interview tips:\n"
            "- Research the company beforehand.\n"
            "- Practice common interview questions.\n"
            "- Dress professionally.\n"
            "- Be confident and clear in your answers."
        )
    
    def has_profile(self) -> bool:
        return self._user_profile["name"] != ""
