from typing import Optional, List, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()


class VideoAnalysis(BaseModel):
    status: Literal["clear", "inconclusive", "multiple_subjects"] = Field(
        description=(
            "Classify whether the video content is clearly understandable. "
            "'clear' if the main subject/action is identifiable, "
            "'multiple_subjects' if there are several distinct focal subjects, "
            "'inconclusive' if the content cannot be determined from the video."
        )
    )
    main_story: str = Field(
        description=(
            "A warm, concise 2–3 sentence description of what happens in the video, "
            "including the mood and any notable moment. Do not assume details not visible."
        )
    )
    kitten_details: Optional[List[str]] = Field(
        default=None,
        description=(
            "Optional short bullet points of distinct visual details (e.g., colors, objects, "
            "clothing, animals, setting). Leave null if not applicable."
        ),
    )


def process_kitten_video(url: str) -> VideoAnalysis | None:
    print(f"\n🎥 Analyzing: {url}")

    try:
        contents = [
            f"Analyze this video: {url}",
            (
                "Describe the video content in a warm, natural tone suitable for a short summary. "
                "Focus on what is visually happening, the mood, and any notable moments. "
                "Do not assume the subject unless clearly visible."
            ),
        ]

        print("\n🧾 PROMPT CONTENTS:")
        for i, c in enumerate(contents, 1):
            print(f"[{i}] {c}")

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VideoAnalysis,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False, thinking_level="minimal"
                ),
            ),
        )
        parsed = response.parsed
        if parsed is None:
            print("⚠️ No parsed payload returned.")
            return None

        if isinstance(parsed, VideoAnalysis):
            data = parsed
        else:
            data = VideoAnalysis.model_validate(parsed)

        if data.status == "inconclusive":
            print("⚠️ Video marked as inconclusive. Skipping...")
            return None

        return data

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    vids = [
        # "https://youtu.be/S3JmDnsPWE8",
        "https://youtu.be/S3JmDnsPWE8"
    ]

    for v in vids:
        result = process_kitten_video(v)
        if result:
            print(result)
            # print(f"✅ STATUS: {result.status}")
            # print(f"📝 BIO: {result.main_story}")
            # if result.kitten_details:
            #     print(f"🔎 DETAILS: {', '.join(result.kitten_details)}")
