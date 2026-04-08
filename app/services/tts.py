import traceback
import re
import io
from concurrent.futures import ThreadPoolExecutor
from google.cloud import texttospeech
from pydub import AudioSegment

from app.config import (
    VOICE_CONFIG,
    VOICE_DEFAULT,
    TTS_SPEAKING_RATE,
    TTS_PITCH,
    TTS_EFFECTS_PROFILE,
)

from app.services.sfx import get_sfx_file

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = texttospeech.TextToSpeechClient()
    return _client


# =============================================================================
# SAFE SANITIZE (SSML SAFE)
# =============================================================================
def _sanitize_text(text: str) -> str:
    text = re.sub(r'\n+', ' ', text)
    text = text.replace("&", "and")
    text = re.sub(r'[^\x09\x0A\x0D\x20-\x7F\u0900-\u097F]', '', text)
    return text.strip()


# =============================================================================
# EXTRACT SFX TAGS
# =============================================================================
def _extract_sfx(text: str):
    matches = re.findall(r"\[SOUND\](.*?)\[/SOUND\]", text)
    clean_text = re.sub(r"\[SOUND\].*?\[/SOUND\]", "", text)
    return clean_text, matches


# =============================================================================
# SENTENCE SPLIT
# =============================================================================
def _split_sentences(text: str):
    return re.split(r'(?<=[.!?।])\s+', text)


# =============================================================================
# EMOTION ENGINE (UPGRADED)
# =============================================================================
def _apply_emotion(sentence: str) -> str:
    s = sentence.lower()

    if "!" in sentence:
        return f"<prosody rate='1.15' pitch='+4st'>{sentence}</prosody>"

    if "?" in sentence:
        return f"<prosody rate='0.9' pitch='+2st'>{sentence}</prosody>"

    if any(w in s for w in ["अचानक", "खतरा", "danger"]):
        return f"<prosody rate='0.75' pitch='-2st'>{sentence}</prosody>"

    if any(w in s for w in ["हाहा", "oops", "अरे"]):
        return f"<prosody rate='1.2' pitch='+3st'>{sentence}</prosody>"

    if any(w in s for w in ["शेर", "lion"]):
        return f"<prosody rate='0.9' pitch='-3st'>{sentence}</prosody>"

    if any(w in s for w in ["खरगोश", "rabbit"]):
        return f"<prosody rate='1.2' pitch='+4st'>{sentence}</prosody>"

    return f"<prosody rate='1.0'>{sentence}</prosody>"


# =============================================================================
# BUILD SSML
# =============================================================================
def _build_ssml(text: str) -> str:
    text = _sanitize_text(text)
    sentences = _split_sentences(text)

    final = ""

    for s in sentences:
        if not s.strip():
            continue

        styled = _apply_emotion(s.strip())

        styled = styled.replace("।", "। <break time='300ms'/>")
        styled = styled.replace(".", ". <break time='300ms'/>")
        styled = styled.replace("!", "! <break time='550ms'/>")
        styled = styled.replace("?", "? <break time='450ms'/>")

        final += styled + " "

    return f"<speak>{final}</speak>"


# =============================================================================
# SMART CHUNKING
# =============================================================================
def _split_text(title: str, story: str):
    full = f"{title}. {story}"
    sentences = _split_sentences(full)

    chunks = []
    current = ""

    for s in sentences:
        if len(current) + len(s) < 1500:
            current += " " + s
        else:
            chunks.append(current.strip())
            current = s

    if current:
        chunks.append(current.strip())

    return chunks


# =============================================================================
# PARALLEL TTS
# =============================================================================
def _synthesize_chunk(chunk, voice_cfg):
    ssml = _build_ssml(chunk)

    return _get_client().synthesize_speech(
        input=texttospeech.SynthesisInput(ssml=ssml),
        voice=texttospeech.VoiceSelectionParams(
            language_code=voice_cfg["language_code"],
            name=voice_cfg["name"],
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=TTS_SPEAKING_RATE,
            pitch=TTS_PITCH,
            effects_profile_id=TTS_EFFECTS_PROFILE,
        ),
    ).audio_content


# =============================================================================
# JOIN AUDIO
# =============================================================================
def _join_audio(segments):
    return b"".join(segments)


# =============================================================================
# SFX OVERLAY ENGINE
# =============================================================================
def _overlay_sfx(base_audio: bytes, sfx_tags: list[str]) -> bytes:
    audio = AudioSegment.from_file(io.BytesIO(base_audio), format="mp3")

    for i, tag in enumerate(sfx_tags):
        sfx_path = get_sfx_file(tag)
        if not sfx_path:
            continue

        try:
            sfx = AudioSegment.from_file(sfx_path)
            position = int((i + 1) * len(audio) / (len(sfx_tags) + 1))
            audio = audio.overlay(sfx, position=position)
        except:
            continue

    output = io.BytesIO()
    audio.export(output, format="mp3")
    return output.getvalue()


# =============================================================================
# MAIN
# =============================================================================
def generate_audio(title: str, story: str, language: str) -> bytes:
    voice_cfg = VOICE_CONFIG.get(language.strip().capitalize(), VOICE_DEFAULT)

    clean_story, sfx_tags = _extract_sfx(story)

    chunks = _split_text(title, clean_story)
    print(f"🎙️ chunks: {len(chunks)} | sfx: {len(sfx_tags)}")

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            audio_segments = list(executor.map(
                lambda c: _synthesize_chunk(c, voice_cfg),
                chunks
            ))

        final_audio = _join_audio(audio_segments)

        if sfx_tags:
            final_audio = _overlay_sfx(final_audio, sfx_tags)

        return final_audio

    except Exception as e:
        print(f"❌ TTS FAILED: {e}")
        traceback.print_exc()

        response = _get_client().synthesize_speech(
            input=texttospeech.SynthesisInput(text=f"{title}. {story}"),
            voice=texttospeech.VoiceSelectionParams(
                language_code=voice_cfg["language_code"],
                name=voice_cfg["name"],
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
            ),
        )

        return response.audio_content