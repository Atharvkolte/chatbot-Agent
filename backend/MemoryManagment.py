from pymongo import MongoClient
import datetime

class memoryManager:
    def __init__(self):
        self.connection_str="mongodb+srv://AI_db:bjHIZzJR2oXjss9o@cluster0.ylzlj16.mongodb.net/?retryWrites=true&w=majority"


    def last10msg(self, thread_id=0):
        memory = ""
        client = MongoClient(self.connection_str)
        db = client["ChatHistory"]
        collection = db["ChatHistory"+str(thread_id)]
        cursor = collection.find().sort("_id", -1).limit(10)
        
        # The cursor returns documents in reverse order (newest first) due to sort("_id", -1)
        # We might want to construct the memory in chronological order.
        # Let's collect them and reverse.
        messages = list(cursor)
        messages.reverse()
        
        for doc in messages:
            memory += "User: " + str(doc.get("user")) + "\nAssistant: " + str(doc.get("assistant")) + "\n"
        return memory

    def get_summary(self, thread_id=0):
        client = MongoClient(self.connection_str)
        db = client["ChatHistory"]
        collection = db["ChatHistory"+str(thread_id)]
        cursor = collection.find_one({"_id": "summary"})
        if cursor:
            return cursor.get("summary")
        return ""
        
    def storeMSG(self, user_input, assistant_response, metadata, thread_id=0):
        client = MongoClient(self.connection_str)
        db = client["ChatHistory"]
        collection = db["ChatHistory"+str(thread_id)]
        
        document = {
            "user": user_input,
            "assistant": assistant_response,
            "metadata": metadata,
            "timestamp": datetime.datetime.utcnow()
        }
        collection.insert_one(document)
            

    def store_summary(self,summary,metadata,thread_id=0):
        client = MongoClient(self.connection_str)
        db = client["ChatHistory"]
        collection = db["ChatHistory"+str(thread_id)]
        filter_doc = {"_id": "summary"}
        update_doc = {
            "$set": {
                "summary": summary,
                "metadata": metadata,
                "timestamp": datetime.datetime.utcnow()
            }
        }
        collection.update_one(filter_doc, update_doc, upsert=True)

def main():
    memory_manager = memoryManager()
    # Test
    # memory_manager.storeMSG("Hello", "Hi there!", {}, 0)
    print(memory_manager.last10msg())

if __name__ == "__main__":
    main()