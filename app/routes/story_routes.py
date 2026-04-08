import uuid
import time
import traceback
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.models.story_model import StoryRequest, StoryResponse, StoryData
from app.core.story_pipeline import run_story_pipeline
from app.db.firestore import db

router = APIRouter(prefix="/story")


# =============================================================================
# POST /story/get
# =============================================================================
@router.post("/get", response_model=StoryResponse)
async def get_story(data: StoryRequest):
    request_id = str(uuid.uuid4())
    start = time.time()

    print(f"📥 [{request_id}] {data.language} | {data.age_group} | '{data.theme}'")

    try:
        result = await run_in_threadpool(
            run_story_pipeline,
            data.language,
            data.theme,
            data.age_group,
        )

        api_duration = round(time.time() - start, 2)

        if not result["ok"]:
            print(f"❌ [{request_id}] Pipeline error: {result['error']}")
            return StoryResponse(
                status="error",
                request_id=request_id,
                message=result["error"],
                duration_seconds=api_duration,
            )

        print(f"✅ [{request_id}] Done in {api_duration}s | tts={result['tts_status']}")

        return StoryResponse(
            status="success",
            request_id=request_id,
            duration_seconds=api_duration,
            data=StoryData(
                title=result["title"],
                story=result["story"],
                audio_url=result["audio_url"],
                tts_status=result["tts_status"],
                language=result["language"],
                age_group=result["age_group"],
                theme=result["theme"],
                duration_seconds=result.get("duration_seconds", 0.0),
            ),
        )

    except Exception as e:
        api_duration = round(time.time() - start, 2)
        print(f"❌ [{request_id}] Unhandled exception: {e}")
        traceback.print_exc()
        return StoryResponse(
            status="error",
            request_id=request_id,
            message="An unexpected error occurred. Please try again.",
            duration_seconds=api_duration,
        )


# =============================================================================
# GET /story/all
# =============================================================================
@router.get("/all")
async def get_all_stories():
    try:
        docs = (
            db.collection("stories")
            .order_by("created_at", direction="DESCENDING")
            .limit(50)
            .stream()
        )

        return [
            {
                "id": doc.id,
                **{
                    k: str(v) if k == "created_at" else v
                    for k, v in doc.to_dict().items()
                },
            }
            for doc in docs
        ]

    except Exception as e:
        print(f"❌ /story/all error: {e}")
        return {"error": str(e)}