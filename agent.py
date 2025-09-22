from __future__ import annotations
import asyncio
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    AgentSession,
)
from livekit.plugins import openai
from dotenv import load_dotenv
import os
from typing import Annotated

from dbi_driver import DatabaseDriver  # your user profile DB driver
from assistant_fnc import AssistantFnc  # your profile assistant class with LLM function calls
from prompts import INSTRUCTIONS, WELCOME_MESSAGE, LOOKUP_PROFILE_MESSAGE

load_dotenv()

# Initialize database driver (singleton)
DB = DatabaseDriver()

# Extend AssistantFnc to integrate DB calls for user profile lookup and update
class FullAssistantFnc(AssistantFnc):
    def __init__(self):
        super().__init__()

    @llm.ai_callable(description="Look up user profile by name")
    async def lookup_profile(self, name: Annotated[str, llm.TypeInfo(description="User's name to look up")]):
        profile = DB.get_user_profile(name)
        if profile is None:
            return "Profile not found. Please provide your details to create a new profile."
        self._user_profile = {
            "name": profile.name,
            "school": profile.school,
            "interview_status": profile.interview_status
        }
        return f"Profile found:\n{self.get_profile_str()}"

    @llm.ai_callable(description="Create user profile")
    async def create_profile(
        self,
        name: Annotated[str, llm.TypeInfo(description="User's name")],
        school: Annotated[str, llm.TypeInfo(description="User's school")],
        interview_status: Annotated[str, llm.TypeInfo(description="Interview status or notes")]
    ):
        DB.create_user_profile(user_id=name.lower().replace(" ", "_"), name=name, school=school, interview_status=interview_status)
        self._user_profile.update({
            "name": name,
            "school": school,
            "interview_status": interview_status
        })
        return "Profile created successfully!"

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    await ctx.wait_for_participant()

    model = openai.realtime.RealtimeModel(
        instructions=INSTRUCTIONS,
        voice="shimmer",
        temperature=0.7,
        modalities=["audio", "video", "text"]
    )

    fnc = FullAssistantFnc()

    async with AgentSession(
        model=model,
        plugins=[openai.Plugin()],
        function_context=fnc,
    ) as session:

        # Welcome message
        session.conversation.item.create(
            llm.ChatMessage(role="assistant", content=WELCOME_MESSAGE)
        )
        await session.response.create()

        @session.on("user_speech_committed")
        async def on_user_speech_committed(msg: llm.ChatMessage):
            # Normalize user input text
            if isinstance(msg.content, list):
                msg.content = "\n".join(
                    "[media]" if isinstance(x, llm.ChatImage) else str(x) for x in msg.content
                )
            user_text = msg.content.strip()

            # Echo user input back for conversation history
            session.conversation.item.create(
                llm.ChatMessage(role="user", content=user_text)
            )
            await session.response.create()

            # If no profile, try to lookup or prompt for creation
            if not fnc.has_profile():
                if "create profile" in user_text.lower():
                    # Ask user to provide profile details as comma separated values
                    await session.conversation.item.create(
                        llm.ChatMessage(role="assistant",
                            content="Please provide your name, school, and interview status separated by commas."
                        )
                    )
                    await session.response.create()
                else:
                    # Assume user input is name to lookup
                    lookup_response = await fnc.lookup_profile(user_text)
                    await session.conversation.item.create(
                        llm.ChatMessage(role="assistant", content=lookup_response)
                    )
                    await session.response.create()
            else:
                # Profile exists — just respond with profile details for demo
                profile_str = fnc.get_profile_str()
                await session.conversation.item.create(
                    llm.ChatMessage(role="assistant", content=f"Your profile details:\n{profile_str}")
                )
                await session.response.create()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
