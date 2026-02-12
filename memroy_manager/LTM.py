#long term memory manager

import ollama
import psycopg2
from memory_manager.STM import STMManager
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import create_agent
from rank_bm25 import BM25Okapi
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize


class LTMHelper():
    def __init__(self):
        self.stm_manager = STMManager()

    def text_to_embedding(self, text: str) -> list[float]:
        response = ollama.embeddings(
            model="nomic-embed-text",
            prompt=text
        )
        return response["embedding"]

    def prompt_template(self, prompt: str, thread_id=1) -> str:
        previous_memories = self.stm_manager.get_last5_memory(thread_id)
        prompt = f"""
            USER_MESSAGE:
            {prompt}
            EXTRACT FACTS FROM ONLY USER MESSAGE THAT ARE WORTH STORING IN LONG TERM MEMORY.
            IMPORTANT: If there are NO FACTS WORTH STORING, RETURN NOTHING.
            RECENT MEMORY:
            {previous_memories}

        """
        return prompt

    def bm25_rerank(self, query, documents, top_n=5):
        if not isinstance(query, str):
            raise ValueError("BM25 query must be a string")

        tokenized_docs = [word_tokenize(doc.lower()) for doc in documents]
        bm25 = BM25Okapi(tokenized_docs)

        tokenized_query = word_tokenize(query.lower())
        scores = bm25.get_scores(tokenized_query)

        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in ranked[:top_n]]
    


class LTMManager(LTMHelper):
    def __init__(self):
        super().__init__()
        self.conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="postgres",
            user="postgres",
            password="3115"
            # host="db.fqphwylufnxlproekqvp.supabase.co",
            # port=5432,
            # database="postgres",
            # user="postgres",
            # password="#####",
            # sslmode="require"
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

    def storeFacts(self, fact: str)->str:
        """
        Store extracted facts and their embeddings into the PostgreSQL database. cell by cell.
        """
        embedding= self.text_to_embedding(fact)
        query = """
            INSERT INTO facts (fact, fact_embedding)
            VALUES (%s, %s)
        """
        self.cur.execute(query, (fact, embedding))
        self.conn.commit()
        return "Fact stored."

    def extractFacts(self, prompt: str): #imposter
        llm = ChatOllama(
            model="qwen3:1.7b",
            temperature=0.7,
            #base_url="http://host.docker.internal:11434"
        )
        tools = [self.storeFacts]
        agent = create_agent(llm, tools=tools)
        system_prompt = ("""You are a LONG-TERM MEMORY EXTRACTION AGENT.
            Your job:
            - Only Read the USER MESSAGE
            - Decide if any LONG-TERM memory is worth storing

            What counts as LONG-TERM memory:
            - User identity (name, location, role)
            - Stable preferences (likes, dislikes)
            - Ongoing projects or goals
            - Skills, tools, tech stack
            - Persistent constraints

            What does NOT count:
            - Emotions
            - One-time events
            - Temporary states
            - DO NOT include environment data (weather, time, location unless user states it)
            - Questions
            - Chatty text

            Rules:
            - Extract ONLY atomic facts
            - Each fact must be a single short sentence
            - If nothing is worth storing, do NOTHING
            - If storing, CALL storeFacts ONCE PER FACT
            - NEVER explain your decision
            - NEVER talk to the user"""
        )
        prompt=self.prompt_template(prompt)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]

        result = agent.invoke({"messages": messages})

        return result    

    def ragExtract(self,query: str, top_k: int = 5):
        query_embedding = self.text_to_embedding(query)

        sql = """
            SELECT
                fact,
                1 - (fact_embedding <=> %s::vector) AS similarity
            FROM facts
            ORDER BY fact_embedding <=> %s::vector
            LIMIT %s
        """

        self.cur.execute(sql, (query_embedding, query_embedding, top_k))
        rows = self.cur.fetchall()

        return [row[0] for row in rows]

    def rag_bm25ExtractFact(self,query: str, top_k: int = 5, top_n: int = 3):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id SERIAL PRIMARY KEY,
                fact TEXT NOT NULL,
                fact_embedding VECTOR(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );        
        """)
        retrieved_docs = self.ragExtract(query, top_k=top_k)
        reranked_docs = self.bm25_rerank(query, retrieved_docs, top_n=top_n)
        convo_facts=""
        for doc in reranked_docs:
            convo_facts+=doc+"\n"
        return convo_facts




if __name__ == "__main__":
    obj=LTMManager()
    msg="hey tell me about cats"
    print(obj.extractFacts(msg))

