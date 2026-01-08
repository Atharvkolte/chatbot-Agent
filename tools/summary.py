from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

def summary(old_summary: str, new_messages: str) -> str:
    llm = ChatOllama(
        model="llama3.2:3b",
        temperature=0.7,
        #base_url="http://host.docker.internal:11434"
    )

    prompt = f"""
        You are a conversation memory manager for an AI assistant.

        Your task is to maintain an accurate, concise, and factual rolling memory of the user.

        --------------------
        INPUT
        --------------------

        Existing Memory (may be empty):
        {old_summary}

        New Conversation Messages:
        {new_messages}

        --------------------
        INSTRUCTIONS
        --------------------

        1. Carefully read both the existing memory and the new messages.
        2. Update the memory ONLY if the new messages contain:
        - Explicit user facts (name, location, job, education)
        - Long-term preferences (tools, tech stack, interests, habits)
        - Stable goals or ongoing projects
        3. Do NOT invent or guess missing details.
        4. If new information contradicts old memory, replace the old fact.
        5. Ignore:
        - Casual chit-chat
        - One-off opinions
        - Temporary emotions unless repeated consistently

        --------------------
        OUTPUT
        --------------------

        Produce the output in TWO clearly separated sections:

        ### UPDATED USER MEMORY (max 300 words)
        - A clean, third-person summary of all known user facts.
        - Must be factual, compact, and suitable for long-term storage.

        ### SUMMARY OF NEW MESSAGES
        - Brief bullet-point summary of what happened in the new messages.
        - No memory interpretation here.

        Do not include anything else.

    """
    
    messages = [
        SystemMessage(content="You are a helpful assistant that summarizes text."),
        HumanMessage(content=prompt)
    ]

    result = llm.invoke(messages)
    summary_text = result.content

    return summary_text
