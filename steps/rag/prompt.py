from zenml import step


@step
def build_prompt(intent: dict, context: dict) -> str:

    platform = intent["platform"]
    topic = intent["topic"]
    tone = intent["tone"]

    style_context = context.get("style_context", "").strip()
    content_context = context.get("content_context", "").strip()

    prompt = f"""
Write an ORIGINAL {platform} post.

Topic:
{topic}

Tone:
{tone}

STYLE GUIDANCE (for tone and structure only — do NOT copy text):
- Clear, explanatory engineering style
- Uses concrete system design examples
- Slightly conversational, confident tone
- Assumes a technically literate audience
- Ends with a practical takeaway or insight

STYLE EXAMPLES (for inspiration only, do NOT quote or imitate):
{style_context}

REFERENCE MATERIAL (for ideas only — do NOT quote, copy phrasing, or reproduce structure):
{content_context}

Rules (IMPORTANT):
- Do NOT copy or closely paraphrase any text from the examples or reference material
- Do NOT reproduce the same structure, sections, or sequence of ideas
- Generate fully original content inspired only by high-level ideas
- Use your own wording and organization
- Output only the final post content (no explanations)

Now write the post.
""".strip()

    return prompt
