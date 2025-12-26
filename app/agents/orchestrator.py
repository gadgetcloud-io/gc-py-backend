"""
Agent Orchestrator - Core AI agent execution engine
Coordinates Claude API calls with tool execution
"""

import anthropic
import logging
from typing import Dict, List, Any, Optional
from app.core.config import settings
from app.agents.tools import get_tool_definitions, execute_tool

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates AI agent interactions with Claude API
    Manages tool execution and conversation flow
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.model = settings.ANTHROPIC_MODEL
        self.max_iterations = 10  # Prevent infinite loops

    async def execute(
        self,
        user_query: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an agent query with tool use

        Args:
            user_query: The user's natural language query
            user_id: Optional user ID for context
            context: Optional additional context

        Returns:
            Dict containing response text, tool calls, and metadata
        """

        if not self.client:
            return {
                "response": "AI features are not enabled. Please configure ANTHROPIC_API_KEY.",
                "agent_used": False,
                "error": "ai_disabled"
            }

        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(user_id, context)

            # Build user message
            messages = [
                {
                    "role": "user",
                    "content": user_query
                }
            ]

            # Tool definitions
            tools = get_tool_definitions()

            # Execute conversation loop with tool use
            iteration = 0
            tool_calls_made = []

            while iteration < self.max_iterations:
                iteration += 1

                logger.info(f"Agent iteration {iteration}: Calling Claude API")

                # Call Claude
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    tools=tools,
                    messages=messages
                )

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # No more tool calls, return final response
                    text_content = self._extract_text(response.content)
                    return {
                        "response": text_content,
                        "agent_used": True,
                        "tool_calls": tool_calls_made,
                        "model": self.model,
                        "iterations": iteration
                    }

                elif response.stop_reason == "tool_use":
                    # Execute tools and continue conversation
                    tool_results = []

                    for block in response.content:
                        if block.type == "tool_use":
                            logger.info(f"Executing tool: {block.name}")
                            tool_calls_made.append({
                                "tool": block.name,
                                "input": block.input
                            })

                            try:
                                result = await execute_tool(
                                    tool_name=block.name,
                                    tool_input=block.input,
                                    user_id=user_id
                                )
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": str(result)
                                })
                            except Exception as e:
                                logger.error(f"Tool execution error: {e}")
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Error: {str(e)}",
                                    "is_error": True
                                })

                    # Add assistant message and tool results to conversation
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                else:
                    # Unexpected stop reason
                    logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                    break

            # Max iterations reached
            logger.warning(f"Max iterations ({self.max_iterations}) reached")
            return {
                "response": "I apologize, but I need more time to process your request. Please try again or rephrase your question.",
                "agent_used": True,
                "tool_calls": tool_calls_made,
                "error": "max_iterations_reached"
            }

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return {
                "response": "I'm having trouble connecting to the AI service. Please try again later.",
                "agent_used": False,
                "error": str(e)
            }

        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            return {
                "response": "An error occurred while processing your request.",
                "agent_used": False,
                "error": str(e)
            }

    def _build_system_prompt(self, user_id: Optional[str], context: Optional[Dict]) -> str:
        """Build the system prompt with context"""

        prompt = """You are a helpful AI assistant for GadgetCloud, a gadget care and repair platform.

You have access to tools to help users with:
- Finding and managing their gadgets
- Booking repair appointments
- Checking repair status
- General support questions

Always be helpful, concise, and professional. Use tools when needed to provide accurate information.
"""

        if user_id:
            prompt += f"\n\nCurrent user ID: {user_id}"

        if context:
            prompt += f"\n\nAdditional context: {context}"

        return prompt

    def _extract_text(self, content: List[Any]) -> str:
        """Extract text content from Claude response"""
        text_blocks = [block.text for block in content if hasattr(block, 'text')]
        return "\n".join(text_blocks) if text_blocks else ""


# Global instance
orchestrator = AgentOrchestrator()
