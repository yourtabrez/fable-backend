import traceback
from google import genai
from google.genai import types

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_MAX_TOKENS,
)

_client = genai.Client(api_key=GEMINI_API_KEY)


# =============================================================================
# VALIDATION (RELAXED)
# =============================================================================
def _is_valid_story(title: str, story: str) -> bool:
    if not story or not title:
        return False

    # 🔥 relaxed threshold (important for cinematic style)
    if len(story.split()) < 120:
        return False

    return True


# =============================================================================
# PARSER (ROBUST)
# =============================================================================
def _parse_response(raw: str) -> dict:
    lines = [l.strip() for l in raw.splitlines() if l.strip()]

    if not lines:
        return {"title": "", "story": ""}

    # 🔥 always take first line as title
    title = lines[0].replace("*", "").replace("#", "").strip()

    # remove title from story
    story = "\n".join(lines[1:]).strip()

    return {"title": title, "story": story}


# =============================================================================
# DOPAMINE + CINEMATIC PROMPT
# =============================================================================
def _build_prompt(language: str, theme: str, age_group: str) -> str:
    return f"""
You are creating a CARTOON AUDIO STORY for children.

GOAL:
Make the child feel like watching a fun cartoon with sound.

---

STORY PARAMETERS:
- Language: {language}
- Theme: {theme}
- Age group: {age_group}

---

🎯 HOOK (MANDATORY):
Start with excitement, danger, or surprise.
❌ Never start with "एक बार की बात है"
✅ Example: "आज जंगल में कुछ खतरनाक होने वाला था!"

---

🎭 CHARACTER PERSONALITY:
- Lion → loud, angry
- Rabbit → funny, smart
- Child → curious, emotional

Use dialogue to show personality.

---

😂 HUMOR (MANDATORY):
Add at least 2 funny moments:
- silly mistakes
- funny reactions

---

🎬 STYLE:
- Short lines (6–10 words)
- Fast pacing
- 10+ dialogues
- Micro suspense frequently

---

🔊 SOUND TAGS:
Use:
[SOUND]धम[/SOUND]
[SOUND]ठक[/SOUND]
[SOUND]फुफकार[/SOUND]
[SOUND]हँसी[/SOUND]

---

🔥 CLIMAX:
- Fast
- Loud
- High tension

---

RULES:
- No narration heavy text
- Prefer dialogue
- Simple spoken language

---

OUTPUT:
- First line = title
- Then story
- No extra explanation
"""

# =============================================================================
# FALLBACK STORY (NEVER FAIL UX)
# =============================================================================
def _fallback_story(language: str):
    return {
        "title": "छोटा सा रोमांच",
        "story": """[SOUND]धम![/SOUND]
एक ज़ोर की आवाज़ हुई।

एक छोटा बच्चा डर गया।
उसका दिल तेज़ धड़कने लगा।

"कौन है वहाँ?" उसने पूछा।

और तभी...
कुछ हिला।

[SOUND]सर्र![/SOUND]

वो धीरे-धीरे आगे बढ़ा।

और अचानक—
उसे एक छोटा दोस्त मिल गया।

वो डर नहीं था।
वो दोस्ती थी।

दोनों हँसने लगे।

और दिन खुशियों से भर गया।""",
        "_error": None,
    }


# =============================================================================
# MAIN GENERATION
# =============================================================================
def generate_story(language: str, theme: str, age_group: str) -> dict:
    prompt = _build_prompt(language, theme, age_group)

    for attempt in range(2):
        try:
            response = _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=GEMINI_TEMPERATURE,
                    max_output_tokens=GEMINI_MAX_TOKENS,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )

            raw = getattr(response, "text", "").strip()

            print(f"🔍 Gemini attempt {attempt + 1} | chars={len(raw)}")
            print("❗ RAW SAMPLE:", raw[:300])

            if not raw:
                continue

            parsed = _parse_response(raw)

            if _is_valid_story(parsed["title"], parsed["story"]):
                return {**parsed, "_error": None}

        except Exception as e:
            print(f"❌ Gemini error: {e}")
            traceback.print_exc()

    print("⚠️ Using fallback story")

    return _fallback_story(language)