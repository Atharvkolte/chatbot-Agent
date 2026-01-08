import datetime
from unittest import result
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import create_agent
from memroy_manager import STMManager
from tools import (
    get_weather,
)


# -------------------- OLLAMA GPT --------------------
class OllamaGpt:
    def __init__(self):
        self.llm = ChatOllama(
            model="qwen3:8b",
            temperature=0.7,
            #base_url="http://host.docker.internal:11434"
        )

        self.tools = [
            get_weather
        ]
        self.agent = create_agent(self.llm, tools=self.tools)

        self.system_prompt = (
            "You are a helpful assistant.\n"
            "IMPORTANT RULES:\n"
            "- Treat explicit user statements about themselves "
            "(name, location, profession) as FACTS.\n"
            "- Do NOT hedge or infer when the user has explicitly stated a fact.\n"
            "- If the user said 'I live in X', always answer confidently.\n"
        )
        self.stm_manager = STMManager()


    def prompt_template(self, user_input: str, thread_id=0) -> str:
        summary = self.stm_manager.get_latest_summary(thread_id)
        print("=== Current Summary ===")
        previous_memories = self.stm_manager.get_last5_memory(thread_id)
        prompt = f"""
            You are an AI assistant continuing an ongoing conversation.

            ### Conversation Summary (High-level, authoritative)
            {summary}

            ### Recent Conversation Memory (Last 5 turns, may be incomplete)
            {previous_memories}

            ### Current User Input
            {user_input}

            ### Instructions
            - Use the summary as the primary source of truth.
            - Use recent memory only if relevant.
            - Respond clearly and helpfully.
        """

        return prompt

    def generate_response(self, user_input: str, thread_id=0)->str:
        prompt = self.prompt_template(user_input, thread_id)
        #prompt = user_input
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]

        result = self.agent.invoke({"messages": messages})
        response=result["messages"][-1].content
        
        self.commandToExecute(user_input, response, thread_id)

        return response

    def commandToExecute(self, user_input: str, response: str, thread_id=0):
        self.stm_manager.create_memory_table(user_input, response, thread_id)


# -------------------- MAIN --------------------
def main():
    bot = OllamaGpt()
    print("🤖 OllamaGPT running with qwen2.5:3b")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response = bot.generate_response(user_input)
        print("Bot:", response)
        print("-" * 40)

    bot.stm_manager.close()

if __name__ == "__main__":
    main()