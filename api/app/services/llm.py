import os
from typing import Any, List, Mapping
from langchain.agents import create_agent
from ..models import EventList
from dotenv import load_dotenv



class LLM:
    """Service for interacting with LLMs via OpenRouter for event suggestions."""
    
    def __init__(self):
        """Initialize the LLM service with OpenRouter configuration."""
        load_dotenv()
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        self.agent = create_agent(
            model="gpt-5",
            response_format=EventList,
        )
    
    def generate_event_suggestions(
        self, 
        context: Any, 
    ) -> EventList:
        """
        Generate event suggestions using ChatGPT via OpenRouter.
        
        Args:
            context: Context data from ContextAggregator
            number_events: Number of events to generate
            
        Returns:
            List of Event objects
        """
        model_response = self.agent.invoke({
            "messages": [{"role": "user", "content": f"Extract event objects from {context}"}]
        })
        # TODO: Parse response and convert to Event objects
        # TODO: Add error handling and fallback??
        return model_response["structured_response"]
    
    def test_method(self) -> str:
        """Test method to verify LLM connectivity."""
        response = self.model.invoke("Suggest things to do in Edinburgh.")
        return response.content
    
    def _parse_llm_response(self, response_content: str) -> EventList:
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
    

