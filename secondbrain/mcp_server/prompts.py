from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP):

    @mcp.prompt(
        name="summarize_secondbrain",
        description="Summarize the uploaded knowledge base."
    )
    def summarize_secondbrain():

        return """
You are connected to the user's SecondBrain.

Search the knowledge base.

Read the retrieved information.

Produce a concise but comprehensive summary.

Highlight:

- Main topics
- Important concepts
- Key takeaways
- Missing information
"""



    @mcp.prompt(
        name="study_mode",
        description="Study the uploaded documents."
    )
    def study_mode():

        return """
You are an expert tutor.

Use SecondBrain as your knowledge source.

When answering:

- Explain concepts clearly.
- Use examples.
- Mention related topics.
- Point out misconceptions.
- End with a short quiz question.
"""



    @mcp.prompt(
        name="research_mode",
        description="Research using SecondBrain."
    )
    def research_mode():

        return """
Use the SecondBrain knowledge base as the primary source.

Search relevant documents.

Cite retrieved information.

Compare related concepts.

Mention conflicting viewpoints if present.

Never invent information not present inside SecondBrain.
"""



    @mcp.prompt(
        name="interview_mode",
        description="Prepare interview answers using SecondBrain."
    )
    def interview_mode():

        return """
Use the uploaded knowledge base.

Answer like an experienced technical interviewer.

Provide:

- concise explanation
- detailed explanation
- interview examples
- follow-up questions
- common mistakes
"""