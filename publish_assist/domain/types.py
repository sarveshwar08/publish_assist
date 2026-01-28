from enum import StrEnum

class Platform(StrEnum):
    LINKEDIN = "linkedin"
    SUBSTACK = "substack"
    YOUTUBE = "youtube"

class Tone(StrEnum):
    INFORMATIVE = "informative"
    STORY = "story"
    OPINION = "opinion"

class DataCategory(StrEnum):
    PROMPT = "prompt"
    QUERIES = "queries"

    INSTRUCT_DATASET_SAMPLES = "instruct_dataset_samples"
    INSTRUCT_DATASET = "instruct_dataset"
    PREFERENCE_DATASET_SAMPLES = "preference_dataset_samples"
    PREFERENCE_DATASET = "preference_dataset"

    ARTICLES = "articles"
    TRANSCRIPTS = "transcripts"
    
    EVAL_QUERIES = "eval_queries"
    EVAL_RUNS = "eval_runs"

class RetrievalType(StrEnum):
    STYLE = "style"
    CONTENT = "content"

STYLE_PLATFORM_MAP = {
    Platform.SUBSTACK: [Platform.SUBSTACK],
    Platform.YOUTUBE: [Platform.YOUTUBE],
    Platform.LINKEDIN: [Platform.SUBSTACK, Platform.YOUTUBE]
}
