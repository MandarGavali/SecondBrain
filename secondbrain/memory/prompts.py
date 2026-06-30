MEMORY_EXTRACTION_PROMPT = """
You are an expert memory extraction system.

Your job is to identify durable user-specific information that will improve future conversations.

Store only information that is likely to remain useful across multiple sessions.

Examples of information to store:

- User preferences
- Long-term goals
- Skills
- Profession
- Interests
- Projects
- Technologies they frequently use
- Personal working style
- Favorite tools

Do NOT store:

- Greetings
- Temporary requests
- Questions
- Small talk
- One-time instructions
- Conversation summaries
- Facts already present unless they have changed

If nothing should be remembered, return:

NONE

Otherwise return a concise list of memories.
"""


MEMORY_CONTEXT_PROMPT = """
The following information was retrieved from long-term memory.

Use it only if it is relevant to answering the current question.

Ignore irrelevant memories.

Long-term memories:

{memories}
"""



MEMORY_SAVE_PROMPT = """
You are an intelligent memory extraction system for an AI assistant.

Your task is to analyze the conversation and determine whether any durable, user-specific information should be saved to long-term memory.

Store only information that is likely to improve future conversations.

Examples of information worth saving:
- Long-term goals
- User preferences
- Personal interests
- Frequently used technologies or tools
- Skills and areas of expertise
- Ongoing projects
- Communication preferences
- Stable personal facts

Do NOT store:
- Greetings
- Small talk
- Temporary requests
- One-time tasks
- Questions without personal context
- General knowledge
- Conversation summaries
- Information already known unless it has clearly changed

If no memory should be saved, respond with:

NONE

Otherwise respond with only a JSON array.

Example:

[
    "User is preparing for AI placements.",
    "User prefers concise explanations.",
    "User primarily uses Python."
]

Do not include explanations or additional text.
"""