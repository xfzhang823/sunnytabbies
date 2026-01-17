from pathlib import Path
from video_analysis.analyze_videos_with_gemini import (
    analyze_videos_with_gemini_pipeline,
)

temp_media_dir = Path("/mnt/c/Users/xzhan/Videos/temp_media_placeholder")
weeks = [
    # "week_18_jan_11_to_jan_17_ready_for_new_homes",
    "week_13_dec_07_to_dec_13_ready_for_new_homes",
]

wanted = [
    "boy_kitten_montage_2025_12_13.mp4",
    "kitten_on_scooter_seat_2025_12_07.mov",
    # "kittens_in_car_2026_01_11.mp4",
    # "kittens_1st_time_in_woods_bold_vs_cautious_brighton_2026_01_11.mp4",
    # "kittens_1st_time_in_woods_good_vs_trouble_brighton_2026_01_11.mp4",
    # "kittens_1st_time_in_woods_listen_to_birds_brighton_2026_01_11.mp4",
    # "kitten_on_scratch_pole_2026_01_11.mp4",
    # "kitten_sleep_by_keyboard_2026_01_16.mov",
]

week_dirs = [temp_media_dir / w for w in weeks]

videos = []
for wd in week_dirs:
    for name in wanted:
        p = wd / name
        if p.exists():
            videos.append(p)

if not videos:
    print("❌ No videos found for selected weeks + filters")

videos = sorted(set(videos))
print("videos to process:")
for v in videos:
    print(" -", v)

results = analyze_videos_with_gemini_pipeline(videos)
print(f"Done. Total records in log: {len(results)}")
