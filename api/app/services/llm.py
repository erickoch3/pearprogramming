import os
from typing import Any, List, Mapping
from langchain.chat_models import init_chat_model
from ..models import Event
from dotenv import load_dotenv



class LLM:
    """Service for interacting with LLMs via OpenRouter for event suggestions."""
    
    def __init__(self):
        """Initialize the LLM service with OpenRouter configuration."""
        load_dotenv()
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        self.model = init_chat_model("gpt-4.1")
    
    def generate_event_suggestions(
        self, 
        context: Any, 
        number_events: int
    ) -> List[Event]:
        """
        Generate event suggestions using ChatGPT via OpenRouter.
        
        Args:
            context: Context data from ContextAggregator
            number_events: Number of events to generate
            
        Returns:
            List of Event objects
        """
        model_response = self.model.invoke("Generate a list of things to do in Edinburgh.")
        # TODO: Parse response and convert to Event objects
        # TODO: Add error handling and fallback??
        return model_response.content
    
    def test_method(self) -> str:
        """Test method to verify LLM connectivity."""
        response = self.model.invoke("Suggest things to do in Edinburgh.")
        return response.content
    
    def _parse_llm_response(self, response_content: str) -> List[Event]:
        """
        Parse the LLM response and convert to Event objects.
        
        Args:
            response_content: Raw response from ChatGPT
            
        Returns:
            List of Event objects
        """
        # TODO: Parse JSON response from ChatGPT
        # TODO: Convert parsed data to Event objects
        # TODO: Add validation and error handling
        return []
    
    def _get_fallback_events(self) -> List[Event]:
        """
        Provide fallback events if LLM call fails.
        
        Args:
            number_events: Number of fallback events to return
            
        Returns:
            List of fallback Event objects
        """
        sample_events: List[Event] = [
            Event(
                location=(12, 34),
                name="Community Coding Jams",
                emoji="💻",
                event_score=9,
                description="Pair up with local devs for a collaborative hack session.",
                link="https://example.com/community-coding-jam",
            ),
            Event(
                location=(5, 18),
                name="Art Walk Downtown",
                emoji="🎨",
                event_score=7,
                description="Explore pop-up galleries with live demos from local artists.",
            ),
            Event(
                location=(22, 9),
                name="Gourmet Food Truck Rally",
                emoji="🌮",
                event_score=8,
                description="Taste bites from featured chefs with live music.",
            ),
            Event(
                location=(3, 42),
                name="Outdoor Movie Night",
                emoji="🎬",
                event_score=6,
                description="Bring a blanket for a classic film under the stars.",
                link="https://example.com/outdoor-movie-night",
            ),
        ]
        return sample_event

