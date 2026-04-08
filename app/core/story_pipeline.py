import traceback
from datetime import datetime, timezone

from app.services.gemini import generate_story
from app.services.tts import generate_audio
from app.services.storage import upload_audio
from app.db.firestore import db


# =============================================================================
# HELPERS
# =============================================================================
def _estimate_duration(story: str) -> float:
    """
    Estimates audio duration in seconds.
    Based on ~150 words per minute at 0.85 speaking rate.
    """
    word_count = len(story.split())
    return round((word_count / 150) * 60, 1)


# =============================================================================
# PIPELINE
# =============================================================================
def run_story_pipeline(language: str, theme: str, age_group: str) -> dict:
    """
    Orchestrates: Gemini → TTS → GCS → Firestore.
    Never raises — all failures returned as structured error dicts.
    """

    # =========================================================================
    # STEP 1: GENERATE STORY
    # =========================================================================
    print(f"🧠 Pipeline start | lang={language} | theme={theme} | age={age_group}")

    try:
        gemini_result = generate_story(language, theme, age_group)
    except Exception as e:
        print(f"❌ Unexpected Gemini crash: {e}")
        traceback.print_exc()
        return {"ok": False, "error": "Story generation failed unexpectedly."}

    if gemini_result.get("_error"):
        print(f"❌ Gemini returned error: {gemini_result['_error']}")
        return {"ok": False, "error": "Could not generate a valid story. Please try again."}

    title = gemini_result["title"]
    story = gemini_result["story"]
    duration_seconds = _estimate_duration(story)

    # =========================================================================
    # STEP 2: TTS
    # =========================================================================
    audio_url = ""
    tts_status = "failed"

    try:
        audio_bytes = generate_audio(title, story, language)
        audio_url = upload_audio(audio_bytes)
        tts_status = "success"
    except Exception as e:
        print(f"⚠️ Audio pipeline failed: {e}")

    # =========================================================================
    # STEP 3: SAVE TO FIRESTORE (best-effort, never block response)
    # =========================================================================
    try:
        db.collection("stories").add({
            "title": title,
            "story": story,
            "audio_url": audio_url,
            "tts_status": tts_status,
            "language": language,
            "age_group": age_group,
            "theme": theme,
            "duration_seconds": duration_seconds,
            "created_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        print(f"⚠️ Firestore save failed (non-critical): {e}")

    print(f"✅ Pipeline complete | tts={tts_status} | duration={duration_seconds}s")

    return {
        "ok": True,
        "title": title,
        "story": story,
        "audio_url": audio_url,
        "tts_status": tts_status,
        "language": language,
        "age_group": age_group,
        "theme": theme,
        "duration_seconds": duration_seconds,
    }