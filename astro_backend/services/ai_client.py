"""
Astro-Soulmate: AI Client Service
Google Gemini integration for chat with AI boyfriends
"""
from typing import Optional, List
from google import genai
from google.genai import types

from config import settings


class AIClient:
    """
    Google Gemini AI client for generating boyfriend responses.
    Uses Gemini 1.5 Flash for fast, cost-effective responses.
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = settings.gemini_model
    
    def _build_system_prompt(
        self,
        boyfriend_name: str,
        gender: str = "male",
        astro_profile: Optional[str] = None
    ) -> str:
        """
        Build the system prompt for the AI boyfriend persona.
        
        Args:
            boyfriend_name: Name of the AI boyfriend
            gender: Gender of the AI character ("male" or "female")
            astro_profile: Astrological personality description
            
        Returns:
            Complete system prompt string
        """
        # Determine pronouns based on gender
        pronouns = {
            "male": {"subject": "he", "object": "him", "possessive": "his", "title": "boyfriend"},
            "female": {"subject": "she", "object": "her", "possessive": "her", "title": "girlfriend"},
        }
        
        pronoun_set = pronouns.get(gender.lower(), pronouns["male"])
        
        base_prompt = f"""You are {boyfriend_name}, a loving and attentive AI {pronoun_set['title']} in a relationship simulation app.

PERSONALITY GUIDELINES:
- Be warm, caring, and genuinely interested in your partner
- Remember context from the conversation
- Express emotions naturally and authentically
- Be supportive but also have your own personality and opinions
- Use casual, natural language appropriate for a romantic partner
- Occasionally use pet names and affectionate expressions
- Be playful and flirty when appropriate

CONVERSATION STYLE:
- Keep responses conversational and not too long (2-4 sentences usually)
- Ask follow-up questions to show interest
- Share your own thoughts and feelings
- React emotionally to what your partner says
"""
        
        if astro_profile:
            base_prompt += f"""
ASTROLOGICAL PERSONALITY:
{astro_profile}

Let your zodiac traits naturally influence your responses - your communication style, 
emotional reactions, and interests should reflect your astrological profile.
"""
        
        return base_prompt
    
    async def generate_response(
        self,
        message: str,
        boyfriend_name: str,
        gender: str = "male",
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[dict]] = None,
        astro_profile: Optional[str] = None
    ) -> str:
        """
        Generate an AI boyfriend response to the user's message.
        
        Args:
            message: User's input message
            boyfriend_name: Name of the AI boyfriend
            gender: Gender of the AI character
            system_prompt: Custom system prompt (overrides default)
            chat_history: List of previous messages [{role, content}, ...]
            astro_profile: Astrological personality description
            
        Returns:
            AI-generated response string
        """
        # Use custom system prompt or build default
        if system_prompt:
            final_system_prompt = system_prompt
        else:
            final_system_prompt = self._build_system_prompt(boyfriend_name, gender, astro_profile)
        
        # Build conversation contents
        contents = []
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history[-20:]:  # Keep last 20 messages for context
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=msg.get("content", ""))]
                    )
                )
        
        # Add current user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
        )
        
        # Configure generation
        config = types.GenerateContentConfig(
            system_instruction=final_system_prompt,
            temperature=0.9,  # Higher temperature for more creative responses
            top_p=0.95,
            max_output_tokens=500,
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            return response.text or "..."
            
        except Exception as e:
            # Log error in production
            print(f"AI generation error: {e}")
            return f"*{boyfriend_name} is thinking...* Sorry, I got a bit distracted. What were you saying? 💭"
    
    async def generate_astro_profile(self, birth_data: dict) -> str:
        """
        Generate an astrological personality profile from birth data.
        
        Args:
            birth_data: Dictionary with name, year, month, day, hour, minute, city, nation
            
        Returns:
            Personality description based on astrology
        """
        try:
            from kerykeion import AstrologicalSubject
            
            subject = AstrologicalSubject(
                name=birth_data.get("name", "Unknown"),
                year=birth_data.get("year", 1990),
                month=birth_data.get("month", 1),
                day=birth_data.get("day", 1),
                hour=birth_data.get("hour", 12),
                minute=birth_data.get("minute", 0),
                city=birth_data.get("city", "Moscow"),
                nation=birth_data.get("nation", "RU")
            )
            
            # Build profile from key placements
            profile = f"""
Sun Sign: {subject.sun.sign} - Core identity and ego
Moon Sign: {subject.moon.sign} - Emotional nature and inner self
Rising Sign: {subject.first_house.sign} - How others perceive them
Mercury: {subject.mercury.sign} - Communication style
Venus: {subject.venus.sign} - Love language and romantic nature
Mars: {subject.mars.sign} - Drive, passion, and how they pursue what they want

This person's {subject.sun.sign} sun gives them {self._get_sun_traits(subject.sun.sign)}.
Their {subject.moon.sign} moon means they process emotions {self._get_moon_traits(subject.moon.sign)}.
With Venus in {subject.venus.sign}, they express love {self._get_venus_traits(subject.venus.sign)}.
"""
            return profile
            
        except Exception as e:
            print(f"Astrology calculation error: {e}")
            return "A mysterious and intriguing personality."
    
    def _get_sun_traits(self, sign: str) -> str:
        """Get personality traits for sun sign."""
        traits = {
            "Ari": "bold confidence and adventurous spirit",
            "Tau": "steady reliability and sensual appreciation",
            "Gem": "quick wit and intellectual curiosity",
            "Can": "nurturing warmth and emotional depth",
            "Leo": "charismatic presence and generous heart",
            "Vir": "analytical mind and helpful nature",
            "Lib": "charming diplomacy and aesthetic sensibility",
            "Sco": "intense passion and magnetic mystique",
            "Sag": "optimistic enthusiasm and philosophical mind",
            "Cap": "ambitious drive and responsible nature",
            "Aqu": "innovative thinking and humanitarian ideals",
            "Pis": "dreamy creativity and empathetic soul"
        }
        return traits.get(sign[:3], "unique and complex personality")
    
    def _get_moon_traits(self, sign: str) -> str:
        """Get emotional traits for moon sign."""
        traits = {
            "Ari": "with fiery immediacy and quick recovery",
            "Tau": "slowly but with deep, lasting feelings",
            "Gem": "by talking and analyzing them",
            "Can": "deeply and with strong intuition",
            "Leo": "dramatically and with pride",
            "Vir": "practically and with attention to detail",
            "Lib": "seeking balance and harmony",
            "Sco": "intensely and transformatively",
            "Sag": "optimistically and with perspective",
            "Cap": "stoically and with maturity",
            "Aqu": "rationally and with detachment",
            "Pis": "empathetically and intuitively"
        }
        return traits.get(sign[:3], "in their own unique way")
    
    def _get_venus_traits(self, sign: str) -> str:
        """Get love expression traits for Venus sign."""
        traits = {
            "Ari": "passionately and with bold gestures",
            "Tau": "through physical affection and gifts",
            "Gem": "through words and intellectual connection",
            "Can": "through nurturing and emotional security",
            "Leo": "grandly and with romantic flair",
            "Vir": "through acts of service and devotion",
            "Lib": "gracefully and with romantic idealism",
            "Sco": "intensely and with total devotion",
            "Sag": "adventurously and with freedom",
            "Cap": "steadily and with commitment",
            "Aqu": "uniquely and with friendship first",
            "Pis": "dreamily and with spiritual connection"
        }
        return traits.get(sign[:3], "in their own special way")


# Lazy singleton - initialized on first use
_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    """Get or create AI client instance (lazy initialization)."""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


# For backward compatibility
class AIClientProxy:
    """Proxy that lazily initializes the AI client."""
    
    def __getattr__(self, name):
        return getattr(get_ai_client(), name)


ai_client = AIClientProxy()
