#short term memory manager

import psycopg2
from tools.summary import summary

class STMManager:
    def __init__(self):
        # 1. Connect to PostgreSQL
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
            # password="######",
            # sslmode="require"
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()


    def create_memory_table(self, prompt: str, response: str, thread_id: int):
        # Create a table for the specific thread
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS memory_{} (
                id SERIAL PRIMARY KEY,
                prompt TEXT,
                response TEXT
            );
        """.format(thread_id))

        # Insert the prompt and response into the table
        self.cur.execute("""
            INSERT INTO memory_{} (prompt, response)
            VALUES (%s, %s);
        """.format(thread_id), (prompt, response))

        self.cur.execute(f"SELECT COUNT(*) FROM memory_{thread_id};") # why this because some user delete the msg that context should not add up
        last_id = self.cur.fetchone()[0]
        if(last_id % 5 == 0):
            self.upsert_summary(thread_id)

        # Commit changes
        self.conn.commit()
    

    def upsert_summary(self, thread_id: int):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS summary_{} (
                id SERIAL PRIMARY KEY,
                summary TEXT,
                updated_at TIMESTAMP DEFAULT now()
            );
        """.format(thread_id))
        self.conn.commit()
        self.cur.execute("""SELECT summary FROM summary_{} ORDER BY id DESC LIMIT 1""".format(thread_id))
        row = self.cur.fetchone()
        previous_summary = row[0] if row else ""
        summarized=summary(previous_summary,self.get_last5_memory(thread_id))
        self.cur.execute(f"""
            INSERT INTO summary_{thread_id} (summary)
            VALUES (%s)
        """, (summarized,))
        self.conn.commit()
        print("Summary updated for thread", thread_id)

    def get_latest_summary(self, thread_id: int):
        self.cur.execute(f"""
            CREATE TABLE IF NOT EXISTS summary_{thread_id} (
                id SERIAL PRIMARY KEY,
                summary TEXT,
                updated_at TIMESTAMP DEFAULT now()
            );
        """)
        self.conn.commit()

        self.cur.execute(f"""SELECT summary FROM summary_{thread_id} ORDER BY id DESC LIMIT 1""")
        row = self.cur.fetchone()
        return row[0] if row else "No prior summary available."


    def get_memory(self, thread_id: int):
        # Ensure table exists BEFORE selecting
        self.cur.execute(f"""
            CREATE TABLE IF NOT EXISTS memory_{thread_id} (
                id SERIAL PRIMARY KEY,
                prompt TEXT,
                response TEXT
            );
        """)
        self.conn.commit()

        self.cur.execute(f"SELECT prompt, response FROM memory_{thread_id};")
        memories = self.cur.fetchall()

        conversation_history = ""
        for user_msg, bot_msg in memories:
            conversation_history += f"User: {user_msg}\nAssistant: {bot_msg}\n"

        return conversation_history

    def get_last5_memory(self, thread_id: int, max_memories=5):
        # Ensure table exists
        self.cur.execute(f"""
            CREATE TABLE IF NOT EXISTS memory_{thread_id} (
                id SERIAL PRIMARY KEY,
                prompt TEXT,
                response TEXT
            );
        """)
        self.conn.commit()

        # Fetch last N messages (most recent first)
        self.cur.execute(f"""
            SELECT prompt, response
            FROM memory_{thread_id}
            ORDER BY id DESC
            LIMIT %s;
        """, (max_memories,))

        memories = self.cur.fetchall()

        # Reverse so conversation flows old → new
        memories.reverse()

        conversation_history = ""
        for user_msg, bot_msg in memories:
            conversation_history += (
                f"User: {user_msg}\n"
                f"Assistant: {bot_msg}\n"
            )

        return conversation_history


    def close(self):
        self.cur.close()
        self.conn.close()   


if __name__ == "__main__":
    stm_manager = STMManager()
    memories = stm_manager.get_memory(thread_id=0)
    conversation_history = ""
    for idx, memory in enumerate(memories):
        # memory structure: (id, prompt, response)
        user_msg = memory[1]  # prompt column
        bot_msg = memory[2]   # response column
        conversation_history += f"User: {user_msg}\nAssistant: {bot_msg}\n"

    print(conversation_history)
    stm_manager.close()
    

