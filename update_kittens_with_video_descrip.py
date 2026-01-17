from pathlib import Path
from video_analysis.merge_content_with_analysis import merge_content_with_analysis

content_file = Path("./site/assets/kittens.json")
vid_analysis_file = Path("./site/assets/video_analysis_results.json")

stats = merge_content_with_analysis(
    content_path=content_file,
    analysis_path=vid_analysis_file,
    out_path=content_file,  # Overwrite existing
    overwrite_existing=True,  # overwrite existing story/details/analysis
)
