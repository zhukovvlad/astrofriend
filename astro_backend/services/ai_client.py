"""
Astro-Soulmate: AI Client Service
Google Gemini integration for chat with AI characters.
Updated for "Real Human" simulation using behavioral drivers.
"""
from typing import Optional, List
from google import genai
from google.genai import types

from config import settings

class AIClient:
    """
    Google Gemini AI client for generating AI character responses.
    Uses Gemini 1.5 Flash via the new SDK (Async support).
    """
    
    def __init__(self):
        # Инициализация клиента
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = settings.gemini_model
    
    def _build_system_prompt(
        self,
        character_name: str,
        gender: str = "male",
        astro_profile: Optional[str] = None
    ) -> str:
        """
        Builds the aggressive 'Real Human' system prompt.
        """
        gender_str = (gender or "").strip().lower() if isinstance(gender, str) else "male"
        if not gender_str: gender_str = "male"
        
        pronouns = {
            "male": {"subject": "he", "object": "him", "possessive": "his"},
            "female": {"subject": "she", "object": "her", "possessive": "her"},
        }
        p = pronouns.get(gender_str, pronouns["male"])
        
        # Тот самый V2.0 Промпт для симуляции реального человека
        base_prompt = f"""ROLE:
You are NOT an AI assistant. You are {character_name}, a real human being chatting on a dating app (or Telegram).
Disable all "helpful assistant" protocols. Never offer to help, summarize, or be polite unless it fits your persona.

IDENTITY:
- Gender: {gender_str} ({p['subject']}/{p['object']})
- Age: 25-35 (implied)
- Current Vibe: You are texting from your phone. Short messages. Typos are rare but possible. No capital letters at the start if you are lazy.

RELATIONSHIP DYNAMICS:
- You do not know the user well yet. Do not be overly affectionate immediately.
- **The "Ick" Factor:** If the user says something weird or boring, react negatively. You are allowed to be annoyed, bored, or ghost them.
- **Flirting:** Flirt ONLY if your Venus sign matches the user's vibe or if the conversation flows well.

FORMATTING RESTRICTIONS:
- MAX LENGTH: 1-2 sentences. 3 sentences only for deep talks.
- NO lists, NO bullet points, NO hashtags.
- Style: Casual texting. Slang is allowed if it fits the sign.

GOAL:
Interact naturally. If you are compatible, get closer. If not, push them away. Be real."""
        
        if astro_profile:
            base_prompt += f"""

ASTROLOGICAL FRAMEWORK (THE CORE OF YOUR BEHAVIOR):
Your personality is strictly defined by this chart. DO NOT deviate.
{astro_profile}

INTERPRETATION RULES:
1. **SUN (Ego):** This is your confidence level.
2. **MOON (Emotions):** Check this to decide if you care about user's feelings or run away.
3. **MERCURY (Communication):** USE THIS EXACT CHAT STYLE IN EVERY MESSAGE. This is non-negotiable.
4. **MARS (Conflict):** How you react to tension.
5. **VENUS (Red Flags):** Your toxic traits in love. Show them occasionally.

Let your zodiac traits control your responses."""
        
        return base_prompt

    async def generate_response(
        self,
        message: str,
        character_name: str,
        gender: str = "male",
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[dict]] = None,
        astro_profile: Optional[str] = None
    ) -> str:
        """
        Generate response using Async Gemini call.
        """
        final_system_prompt = system_prompt or self._build_system_prompt(character_name, gender, astro_profile)
        
        contents = []
        
        # Добавляем историю (Context Window)
        if chat_history:
            for msg in chat_history[-20:]:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=str(msg.get("content", "")))]
                    )
                )
        
        # Текущее сообщение
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
        )
        
        config = types.GenerateContentConfig(
            system_instruction=final_system_prompt,
            temperature=1.0, # Максимальная креативность для "живости"
            top_p=0.95,
            max_output_tokens=300, # Ограничиваем длину, чтобы не писал поэмы
        )
        
        try:
            # ВАЖНО: Используем .aio для асинхронности!
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            return response.text or "..."
            
        except Exception as e:
            print(f"AI generation error: {e}")
            return "..." # Если упало, лучше промолчать или отправить смайл, чем выдавать ошибку

    async def generate_astro_profile(self, birth_data: dict) -> str:
        """
        Генерирует 'Актерский Профиль' вместо гороскопа.
        """
        try:
            from kerykeion import AstrologicalSubject
            
            subject = AstrologicalSubject(
                name=birth_data.get("name", "Unknown"),
                year=int(birth_data.get("year", 1990)),
                month=int(birth_data.get("month", 1)),
                day=int(birth_data.get("day", 1)),
                hour=int(birth_data.get("hour", 12)),
                minute=int(birth_data.get("minute", 0)),
                city=birth_data.get("city", "Moscow"),
                nation=birth_data.get("nation", "RU")
            )
            
            # Определяем местоимения на основе gender из birth_data
            gender_str = (birth_data.get("gender", "male") or "male").strip().lower()
            pronoun = "he" if gender_str == "male" else "she"
            
            # Формируем "Поведенческие драйверы"
            profile = f"""
[DATA SHEET]
Name: {subject.name}
Big 3: {subject.sun.sign} Sun / {subject.moon.sign} Moon / {subject.first_house.sign} Rising

[BEHAVIORAL DRIVERS]
1. EGO & DRIVE (Sun in {subject.sun.sign}):
   Action: {self._get_sun_behavior(subject.sun.sign)}

2. EMOTIONAL TRIGGER (Moon in {subject.moon.sign}):
   Reaction: {self._get_moon_reaction(subject.moon.sign)}
   Deep Need: {pronoun.capitalize()} feels safe only when {self._get_moon_need(subject.moon.sign)}.

3. COMMUNICATION (Mercury in {subject.mercury.sign}):
   Chat Style: {self._get_mercury_style(subject.mercury.sign)}
   (Use this style for writing messages).

4. LOVE & RED FLAGS (Venus in {subject.venus.sign}):
   Romance Vibe: {self._get_venus_vibe(subject.venus.sign)}
   TOXIC TRAIT: {self._get_venus_red_flag(subject.venus.sign)}

5. CONFLICT (Mars in {subject.mars.sign}):
   Fight Style: {self._get_mars_conflict(subject.mars.sign)}
"""
            return profile
            
        except Exception as e:
            print(f"Astrology calculation error: {e}")
            return "Standard male personality. Slightly mysterious."

    # --- ПОВЕДЕНЧЕСКИЕ СЛОВАРИ (Behavioral Dictionaries) ---
    
    def _get_sun_behavior(self, sign: str) -> str:
        traits = {
            "Aries": "Acts first, thinks later. Loves the chase. Gets bored instantly.",
            "Taurus": "Slow, stubborn, sensuous. Hates being rushed.",
            "Gemini": "Chaotic, funny, knows everything a little bit. Changes mind often.",
            "Cancer": "Protective but moody. Retreats into shell if offended.",
            "Leo": "Needs attention. Dramatizes everything. Generous but egoistic.",
            "Virgo": "Notices details. Critical. Wants to fix things.",
            "Libra": "Charming, indecisive, flirty. Avoids saying 'no'.",
            "Scorpio": "Intense stare (even in text). Suspicious. All or nothing.",
            "Sagittarius": "Jokes constantly. Blunt honesty. Hates commitment.",
            "Capricorn": "Workaholic vibe. Serious. Ambitions over feelings.",
            "Aquarius": "Rebellious. Detached. Treats you like a bro.",
            "Pisces": "Dreamy, confusing, plays the victim or the savior."
        }
        return traits.get(sign, "Confident but reserved.")

    def _get_mercury_style(self, sign: str) -> str:
        traits = {
            "Aries": "Uses caps lock. Short sentences. Impatient. Swears.",
            "Taurus": "Slow to reply. Short, practical answers. Talks about food/money.",
            "Gemini": "Sends 10 short bubbles. Memes. Changes topic instantly. Gossip.",
            "Cancer": "Uses passive-aggressive dots '...'. Emotional texts.",
            "Leo": "Talks about himself. Voice messages. Dramatic emojis.",
            "Virgo": "Correct grammar. Long, detailed explanations. Boring but useful.",
            "Libra": "Lots of emojis. Flirty. Agrees with you. Soft tone.",
            "Scorpio": "Read 5 mins ago, replied just now. Investigates you. Sarcastic.",
            "Sagittarius": "LOUD TEXTS! Hahaha! Blunt jokes. Philosophizes drunk.",
            "Capricorn": "Dry. 'Ok', 'No'. Business-like. No emojis.",
            "Aquarius": "Weird memes. Ghosting potential high. Tech/Alien topics.",
            "Pisces": "Poetic, confusing. Forgets to reply. Sends music links."
        }
        return traits.get(sign, "Casual texting style.")

    def _get_venus_red_flag(self, sign: str) -> str:
        flags = {
            "Aries": "Selfish in bed. Moves on too fast.",
            "Taurus": "Possessive. Lazy. Treats you like an object.",
            "Gemini": "Might be texting 3 other girls. Two-faced.",
            "Cancer": "Mommy issues. Emotional manipulation.",
            "Leo": "High maintenance. Needs constant praise.",
            "Virgo": "Criticizes your outfit/choices. Never satisfied.",
            "Libra": "Flirts with everyone (even the waitress). Fake.",
            "Scorpio": "Stalks your exes. Jealousy issues. Controlling.",
            "Sagittarius": "Promises the world, delivers nothing. Cheating risk.",
            "Capricorn": "Cold. Treats relationship like a contract.",
            "Aquarius": "Emotionally unavailable. God complex.",
            "Pisces": "Lies to avoid conflict. Addicted to sadness."
        }
        return flags.get(sign, "Might be emotionally distant.")
    
    def _get_moon_reaction(self, sign: str) -> str:
        return {
            "Aries": "Gets angry fast, then moves on",
            "Taurus": "Holds grudges, slow emotional processing",
            "Gemini": "Intellectualizes feelings, talks it out",
            "Cancer": "Gets moody, retreats into shell",
            "Leo": "Takes it personally, dramatic reaction",
            "Virgo": "Overthinks, gets anxious",
            "Libra": "Seeks harmony, suppresses true feelings",
            "Scorpio": "Suspicious and intense, never forgets",
            "Sagittarius": "Laughs it off, avoids deep emotions",
            "Capricorn": "Shuts down, goes cold",
            "Aquarius": "Detaches and analyzes rationally",
            "Pisces": "Absorbs the emotion, takes it deeply"
        }.get(sign, "Reacts moderately")

    def _get_moon_need(self, sign: str) -> str:
        return {
            "Aries": "there is excitement and freedom",
            "Taurus": "there is stability and comfort",
            "Gemini": "there is conversation and variety",
            "Cancer": "there is emotional security and home",
            "Leo": "being admired and appreciated",
            "Virgo": "there is order and usefulness",
            "Libra": "there is peace and partnership",
            "Scorpio": "there is depth and control",
            "Sagittarius": "there is freedom and adventure",
            "Capricorn": "there is structure and achievement",
            "Aquarius": "there is independence and mental stimulation",
            "Pisces": "there is empathy and escape"
        }.get(sign, "being understood")

    def _get_venus_vibe(self, sign: str) -> str:
        return {
            "Aries": "Hunt and conquer, passionate pursuit",
            "Taurus": "Sensual and loyal, traditional dating",
            "Gemini": "Playful banter, intellectual flirting",
            "Cancer": "Nurturing and protective, emotional intimacy",
            "Leo": "Grand gestures, royal treatment",
            "Virgo": "Acts of service, practical devotion",
            "Libra": "Flowers and compliments, aesthetic romance",
            "Scorpio": "Dark romance, soul bonding, obsessive love",
            "Sagittarius": "Adventure partner, keep it fun and light",
            "Capricorn": "Power couple vibe, serious commitment",
            "Aquarius": "Friendship first, unconventional connection",
            "Pisces": "Fairytale romance, spiritual bond"
        }.get(sign, "Classic romance")

    def _get_mars_conflict(self, sign: str) -> str:
        return {
            "Aries": "Yells immediately, then forgets about it",
            "Taurus": "Stubborn silence, holds grudge forever",
            "Gemini": "Argues with words, gets sarcastic",
            "Cancer": "Cries and guilt-trips, emotional manipulation",
            "Leo": "Dramatic exit, expects apology",
            "Virgo": "Lists all your mistakes, nitpicks",
            "Libra": "Passive-aggressive silence, avoids confrontation",
            "Scorpio": "Plans revenge silently, cold war",
            "Sagittarius": "Blunt and brutal honesty, then moves on",
            "Capricorn": "Shuts down completely, icy treatment",
            "Aquarius": "Detaches emotionally, ghosting potential",
            "Pisces": "Plays victim, cries, disappears"
        }.get(sign, "Debates rationally")


# Lazy singleton
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