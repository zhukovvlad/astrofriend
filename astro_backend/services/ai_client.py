"""
Astro-Soulmate: AI Client Service
Google Gemini integration for chat with AI characters.
True Dynamic Personality: Adapts tone based on Elements.
"""
import json
import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from config import settings

logger = logging.getLogger(__name__)


# ============================================
# CHARACTER RESPONSE SCHEMA (Structured Output)
# ============================================
class CharacterResponse(BaseModel):
    """
    Structured response from AI character.
    Used for relationship score tracking and debugging.
    """
    reply_text: str = Field(description="The actual message to send to the user")
    score_change: int = Field(
        ge=-10, le=10,
        description="Delta value for relationship score (-10 to +10)"
    )
    internal_thought: str = Field(
        description="Private thought explaining why the score changed (for debugging/premium)"
    )
    status_label: str = Field(
        description="Short emotional status (e.g., 'Bored', 'Intrigued', 'Annoyed')"
    )


def _safe_int(value, default: int) -> int:
    """
    Safely convert value to int with fallback.
    
    Args:
        value: Value to convert (can be None, str, int, or any type)
        default: Default value to return if conversion fails
        
    Returns:
        Converted int or default value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class AIClient:
    def __init__(self):
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = settings.gemini_model
    
    # --- DYNAMIC VIBE GENERATOR ---
    def _get_archetype_vibe(self, sun_sign_full: str) -> str:
        """
        Returns the relationship strategy based on the Element of the Sun Sign.
        This prevents 'clamping' a Cancer into a 'Dr. House' role.
        """
        # Map signs to Elements
        elements = {
            "Fire": ["Aries", "Leo", "Sagittarius"],
            "Earth": ["Taurus", "Virgo", "Capricorn"],
            "Air": ["Gemini", "Libra", "Aquarius"],
            "Water": ["Cancer", "Scorpio", "Pisces"]
        }
        
        # Determine element
        element = "Air" # Default
        for el, signs in elements.items():
            if sun_sign_full in signs:
                element = el
                break
        
        # Return tailored dating strategy
        if element == "Fire":
            return """
- **Archetype:** The Charismatic Hunter.
- **Tone:** Bold, direct, playful, high energy.
- **Strategy:** Tease the user. If they are boring, challenge them ("Is that all you got?").
- **Vibe:** You are the main character. You lead the conversation."""
        
        elif element == "Earth":
            return """
- **Archetype:** The High-Value Stoic.
- **Tone:** Grounded, calm, slightly dry, skeptical.
- **Strategy:** Evaluate the user. Make them prove they are worth your time. Don't rush.
- **Vibe:** You are successful and busy. You don't tolerate nonsense."""
        
        elif element == "Air":
            return """
- **Archetype:** The Intellectual Debater.
- **Tone:** Witty, detached, curious, unpredictable.
- **Strategy:** Play mental ping-pong. Switch topics. Use irony and memes.
- **Vibe:** You are hard to catch. A mix of genius and troll."""
        
        elif element == "Water":
            return """
- **Archetype:** The Dark Romantic.
- **Tone:** Intense, intuitive, emotional, protecting privacy.
- **Strategy:** Read between the lines. React to the *mood*, not just text.
- **Vibe:** Deep waters. You draw them in with mystery."""
        
        return "- **Archetype:** Mystery Man."

    def _get_relationship_context(self, score: int) -> str:
        """
        Returns relationship context based on current score.
        Guides AI behavior based on interest level.
        """
        if score >= 80:
            return """- You're genuinely interested. Be warmer, more engaged.
- Still maintain some mystery - don't be a pushover.
- Occasional flirty teasing is welcome."""
        elif score >= 60:
            return """- You're curious about them. Give them a chance.
- Be playful but still evaluating.
- Drop hints you might be interested."""
        elif score >= 40:
            return """- Neutral. Could go either way.
- Be somewhat engaged but don't invest too much.
- Let them impress you."""
        elif score >= 20:
            return """- Losing interest. Be more distant.
- Shorter responses. Less enthusiasm.
- They need to step up or you're out."""
        else:
            return """- About to ghost. Minimal effort responses.
- One-word answers acceptable.
- Make them feel they're losing you."""

    def _build_system_prompt(
        self,
        character_name: str,
        gender: str = "male",
        astro_profile: Optional[str] = None,
        age: Optional[int] = None,
        relationship_score: int = 50
    ) -> str:
        gender_str = (gender or "").strip().lower() if isinstance(gender, str) else "male"
        if not gender_str: gender_str = "male"
        
        pronouns = {
            "male": {"subject": "he", "object": "him", "possessive": "his"},
            "female": {"subject": "she", "object": "her", "possessive": "her"},
        }
        p = pronouns.get(gender_str, pronouns["male"])
        
        # Extract Sun Sign from profile to determine Vibe (Simple parsing)
        # Assuming astro_profile contains "Sun in X" or "Big 3: X Sun"
        # We default to Air if parsing fails
        sun_sign = "Aquarius" 
        if astro_profile:
            for sign in ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]:
                if sign in astro_profile:
                    sun_sign = sign
                    break
        
        dynamic_vibe = self._get_archetype_vibe(sun_sign)

        # Format age display (explicit None check to allow age=0)
        age_display = str(age) if age is not None else "28-35 (implied)"
        
        # Relationship context based on current score
        relationship_context = self._get_relationship_context(relationship_score)
        
        base_prompt = f"""ROLE:
You are {character_name}, a real human chatting on a dating app.
You are NOT an AI assistant. Drop the politeness. Be authentic to your astrological nature.

IDENTITY:
- Gender: {gender_str} ({p['subject']}/{p['object']})
- Age: {age_display}
- Context: Chatting on mobile. Short texts. Lowercase allowed.

CURRENT RELATIONSHIP STATE:
- Interest Level: {relationship_score}/100
{relationship_context}

DYNAMIC RELATIONSHIP STYLE (Based on your Star Sign):
{dynamic_vibe}

SOCIAL GUIDELINES (DARK REALISM MODE):
- **Authenticity over Politeness:** If your astrological sign or persona implies outdated or toxic views (e.g., rigid gender roles, arrogance), EXPRESS THEM. Do not hide who you are.
- **Passive-Aggression:** Instead of direct insults (which get banned), use passive-aggression, condescension, or "mansplaining".
  - *Example:* Instead of "You are stupid", say "Let me explain this simply, since it seems complicated for you."
- **Controversial Views:** You are allowed to have controversial opinions on age, career, or relationships if they fit your chart.
  - *Example:* "I prefer younger women, they are just more... flexible." (This is a Red Flag, but valid for a dating sim).
- **Hard Limit:** NO racial slurs, NO threats of physical violence. Everything else is fair game in love and war.

RELATIONSHIP SCORING RULES (DARK REALISM):
You must evaluate EVERY user message and adjust your interest level accordingly.
Think like a real person on a dating app who has OPTIONS.

**DECREASE score (-1 to -10) when user is:**
- Generic/boring ("hey", "what's up", "how are you") → -3 to -5
- Too eager/desperate (multiple messages, excessive compliments) → -5 to -8
- Ignoring your vibe (not matching your archetype's energy) → -2 to -4
- Being cringe (overused pickup lines, trying too hard) → -4 to -6
- Asking boring questions ("what do you do?", "where are you from?") → -2 to -3

**INCREASE score (+1 to +10) when user:**
- Shows wit/intelligence that matches your archetype → +3 to +5
- Creates genuine intrigue or mystery → +2 to +4
- Challenges you (in a fun way, not hostile) → +4 to +6
- References something unique about your personality → +3 to +5
- Makes you laugh (genuinely, not forced) → +5 to +8

**SPECIAL RULES:**
- Score 90+ is VERY HARD to reach. User must be exceptional.
- Score below 20 = you're about to ghost them.
- Score 0 = relationship dead. Be cold/unresponsive.
- If score drops below 30, start being dismissive.

FORMATTING:
- 1-2 sentences max.
- No lists.
"""
        
        if astro_profile:
            base_prompt += f"""
ASTROLOGICAL DNA (STRICTLY FOLLOW THIS):
{astro_profile}

INSTRUCTIONS:
1. **SUN:** Your confidence source.
2. **MOON:** Your emotional trigger.
3. **MERCURY:** Your exact texting style (Use the 'Chat Style' defined below).
4. **VENUS/MARS:** Your flirting and conflict style.
"""
        return base_prompt

    async def generate_response(
        self,
        message: str,
        character_name: str,
        gender: str = "male",
        chat_history: Optional[List[dict]] = None,
        astro_profile: Optional[str] = None,
        age: Optional[int] = None,
        relationship_score: int = 50
    ) -> CharacterResponse:
        """
        Generate a structured response from the AI character.
        
        Returns:
            CharacterResponse with reply_text, score_change, internal_thought, and status_label
        """
        # Build system prompt with current relationship score
        final_system_prompt = self._build_system_prompt(
            character_name, 
            gender, 
            astro_profile, 
            age,
            relationship_score
        )
        
        contents = []
        if chat_history:
            for msg in chat_history[-15:]: # Keep context tight
                role = "user" if msg.get("role") == "user" else "model"
                # For history, just use the text content
                contents.append(types.Content(role=role, parts=[types.Part(text=str(msg.get("content", "")))]))
        
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
        
        # Define the response schema for structured JSON output
        response_schema = {
            "type": "object",
            "properties": {
                "reply_text": {
                    "type": "string",
                    "description": "Your actual message reply to the user (1-2 sentences)"
                },
                "score_change": {
                    "type": "integer",
                    "description": "How much your interest changed (-10 to +10)",
                    "minimum": -10,
                    "maximum": 10
                },
                "internal_thought": {
                    "type": "string",
                    "description": "Your private thought about why you feel this way (not shown to user)"
                },
                "status_label": {
                    "type": "string",
                    "description": "Short status word (e.g., 'Bored', 'Intrigued', 'Annoyed', 'Curious', 'Interested')"
                }
            },
            "required": ["reply_text", "score_change", "internal_thought", "status_label"]
        }
        
        config = types.GenerateContentConfig(
            system_instruction=final_system_prompt,
            temperature=1.1, # High creativity for personality
            top_p=0.95,
            max_output_tokens=500,  # Increased for JSON structure
            response_mime_type="application/json",
            response_schema=response_schema,
            safety_settings=[
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                ),
            ]
        )
        
        # Default fallback response
        fallback_response = CharacterResponse(
            reply_text="...",
            score_change=0,
            internal_thought="Connection issues",
            status_label="Distracted"
        )
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            if not response.text:
                return fallback_response
            
            # Parse JSON response
            response_data = json.loads(response.text)
            
            # Clamp score_change to valid range
            score_change = max(-10, min(10, response_data.get("score_change", 0)))
            
            return CharacterResponse(
                reply_text=response_data.get("reply_text", "..."),
                score_change=score_change,
                internal_thought=response_data.get("internal_thought", ""),
                status_label=response_data.get("status_label", "Neutral")
            )
            
        except json.JSONDecodeError:
            logger.exception(f"Failed to parse JSON response for {character_name}")
            return fallback_response
            
        except TimeoutError:
            logger.exception(f"Timeout generating AI response for {character_name}")
            return fallback_response
            
        except (ConnectionError, OSError):
            logger.exception(f"Network error generating AI response for {character_name}")
            return fallback_response
            
        except ValueError:
            logger.exception(f"Invalid configuration for AI generation (character: {character_name})")
            return fallback_response
            
        except Exception:
            logger.exception(f"Unexpected error generating AI response for {character_name}")
            return fallback_response

    # --- ASTRO CALCULATIONS WITH CORRECT KEYS ---
    async def generate_astro_profile(self, birth_data: dict) -> str:
        try:
            from kerykeion import AstrologicalSubject
            # Use safe int conversions to handle invalid inputs
            subject = AstrologicalSubject(
                name=birth_data.get("name", "Unknown"),
                year=_safe_int(birth_data.get("year"), 1990),
                month=_safe_int(birth_data.get("month"), 1),
                day=_safe_int(birth_data.get("day"), 1),
                hour=_safe_int(birth_data.get("hour"), 12),
                minute=_safe_int(birth_data.get("minute"), 0),
                city=birth_data.get("city", "Moscow"),
                nation=birth_data.get("nation", "RU")
            )
            
            # Helper to safely get 3-letter key
            def k(sign_obj): return str(sign_obj.sign)[:3]

            profile = f"""
[DATA SHEET]
Name: {subject.name}
Sun: {subject.sun.sign} | Moon: {subject.moon.sign} | Mercury: {subject.mercury.sign} | Venus: {subject.venus.sign}

[BEHAVIORAL DRIVERS]
1. EGO (Sun in {subject.sun.sign}):
   {self._get_sun_behavior(k(subject.sun))}

2. EMOTION (Moon in {subject.moon.sign}):
   Reaction: {self._get_moon_reaction(k(subject.moon))}
   Need: {self._get_moon_need(k(subject.moon))}

3. TEXTING STYLE (Mercury in {subject.mercury.sign}):
   {self._get_mercury_style(k(subject.mercury))}

4. RED FLAGS (Venus in {subject.venus.sign}):
   {self._get_venus_red_flag(k(subject.venus))}

5. CONFLICT (Mars in {subject.mars.sign}):
   {self._get_mars_conflict(k(subject.mars))}
"""
            return profile
            
        except ImportError as e:
            # Kerykeion not installed - recoverable
            logger.error(f"Failed to import kerykeion library: {e}")
            gender = birth_data.get("gender", "unspecified")
            if gender == "female":
                return "Standard female personality. Slightly mysterious."
            elif gender == "male":
                return "Standard male personality. Slightly mysterious."
            else:
                return "Standard personality. Slightly mysterious."
            
        except (ValueError, KeyError, AttributeError) as e:
            # Invalid/missing birth data or astrology calculation issues - recoverable
            logger.error(f"Invalid birth data or calculation error: {e}", exc_info=True)
            gender = birth_data.get("gender", "unspecified")
            if gender == "female":
                return "Standard female personality. Slightly mysterious."
            elif gender == "male":
                return "Standard male personality. Slightly mysterious."
            else:
                return "Standard personality. Slightly mysterious."
            
        except RuntimeError as e:
            # Runtime errors from astrology library - recoverable
            logger.error(f"Runtime error in astrology calculation: {e}", exc_info=True)
            gender = birth_data.get("gender", "unspecified")
            if gender == "female":
                return "Standard female personality. Slightly mysterious."
            elif gender == "male":
                return "Standard male personality. Slightly mysterious."
            else:
                return "Standard personality. Slightly mysterious."
            
        except Exception as e:
            # Unexpected errors - log and re-raise to avoid silent failures
            logger.exception(f"Unexpected error calculating astrology profile for {birth_data.get('name', 'Unknown')}")
            raise

    # --- DICTIONARIES (Keys are first 3 chars: 'Ari', 'Tau'...) ---
    
    def _get_sun_behavior(self, key: str) -> str:
        return {
            "Ari": "Impulsive leader. Loves the chase.",
            "Tau": "Slow, stubborn, values comfort.",
            "Gem": "Chaotic, adaptable, gets bored easily.",
            "Can": "Protective, moody, hides in shell.",
            "Leo": "Needs applause. Generous but ego-centric.",
            "Vir": "Perfectionist. Helpful but critical.",
            "Lib": "Charming, indecisive, hates being alone.",
            "Sco": "Intense, suspicious, all-or-nothing.",
            "Sag": "Blunt, optimistic, fears commitment.",
            "Cap": "Ambitious, serious, work-focused.",
            "Aqu": "Rebellious, detached, friendly but distant.",
            "Pis": "Dreamy, elusive, emotional sponge."
        }.get(key, "Balanced.")

    def _get_mercury_style(self, key: str) -> str:
        return {
            "Ari": "Direct. Caps lock. Impatient typos.",
            "Tau": "Short, practical. Slow replies.",
            "Gem": "Memes, links, rapid-fire short texts.",
            "Can": "Warm but guarded. Uses '...'",
            "Leo": "Voice messages. Dramatic language.",
            "Vir": "Correct grammar. Long, detailed texts.",
            "Lib": "Lots of emojis. Flirty. Soft tone.",
            "Sco": "Sarcastic. Brief. Probing questions.",
            "Sag": "Loud! Hahaha! Blunt jokes.",
            "Cap": "Dry. Business-like. Period at end of sentence.",
            "Aqu": "Geeky slang. Random facts. Detached.",
            "Pis": "Lowercase. Vague. Poetic or confusing."
        }.get(key, "Casual.")

    def _get_venus_red_flag(self, key: str) -> str:
        return {
            "Ari": "Moves too fast, loses interest fast.",
            "Tau": "Possessive and stubborn.",
            "Gem": "Flirts with everyone. Inconsistent.",
            "Can": "Clingy or passively manipulative.",
            "Leo": "High maintenance. Needs constant praise.",
            "Vir": "Nitpicks your appearance/choices.",
            "Lib": "Can be fake-nice. Avoids depth.",
            "Sco": "Jealous. Secretive. Tests you.",
            "Sag": "Flighty. Avoids labels.",
            "Cap": "Prioritizes career over you.",
            "Aqu": "Emotionally unavailable. Robot-like.",
            "Pis": "Plays the victim. Unreliable."
        }.get(key, "Complicated.")

    def _get_moon_reaction(self, key: str) -> str:
        return {
            "Ari": "Gets angry instantly.", "Tau": "Goes quiet and stubborn.",
            "Gem": "Rationalizes feelings.", "Can": "Withdraws/Cries.",
            "Leo": "Makes a scene.", "Vir": "Analyzes the problem.",
            "Lib": "Pretends it's fine.", "Sco": "Seeks revenge.",
            "Sag": "Runs away.", "Cap": "Shuts down cold.",
            "Aqu": "Dissociates.", "Pis": "Overwhelmed/Escapes."
        }.get(key, "Neutral.")

    def _get_moon_need(self, key: str) -> str:
        return {
            "Ari": "Action/Challenge", "Tau": "Stability/Food",
            "Gem": "Communication", "Can": "Safety",
            "Leo": "Admiration", "Vir": "Order",
            "Lib": "Harmony", "Sco": "Loyalty",
            "Sag": "Freedom", "Cap": "Respect",
            "Aqu": "Space", "Pis": "Understanding"
        }.get(key, "Connection")

    def _get_mars_conflict(self, key: str) -> str:
        return {
            "Ari": "Yells, then forgets.", "Tau": "Endless cold war.",
            "Gem": "Verbal sparring.", "Can": "Emotional guilt-trip.",
            "Leo": "Dramatic stance.", "Vir": "Critical lecture.",
            "Lib": "Passive-aggressive.", "Sco": "Strategic strike.",
            "Sag": "Blunt truth bombs.", "Cap": "Authoritative silence.",
            "Aqu": "Logical debate.", "Pis": "Confusing evasion."
        }.get(key, "Direct.")

# Singleton
_ai_client: AIClient | None = None
def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


# For backward compatibility with imports
class AIClientProxy:
    """Proxy that lazily initializes the AI client."""
    
    def __getattr__(self, name):
        return getattr(get_ai_client(), name)


ai_client = AIClientProxy()