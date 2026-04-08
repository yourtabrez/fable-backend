import uuid
import traceback
from google.cloud import storage

from app.config import GCS_BUCKET_NAME

_client = None
_bucket = None


def _get_bucket():
    global _client, _bucket
    if _bucket is None:
        _client = storage.Client()
        _bucket = _client.bucket(GCS_BUCKET_NAME)
    return _bucket


# =============================================================================
# MAIN
# =============================================================================
def upload_audio(audio_bytes: bytes) -> str:
    filename = f"stories/{uuid.uuid4()}.mp3"

    try:
        blob = _get_bucket().blob(filename)
        blob.upload_from_string(audio_bytes, content_type="audio/mpeg")

        url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        print(f"✅ GCS upload | {url}")
        return url

    except Exception as e:
        print(f"❌ GCS upload failed: {e}")
        traceback.print_exc()
        raise