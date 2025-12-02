import os
import requests
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from MemoryManagment import memoryManager

# Define the weather tool
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a specific city."""
    try:
        # 1. Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        if not geo_response.get("results"):
            return f"Could not find coordinates for {city}."
        
        location = geo_response["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        
        # 2. Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_response = requests.get(weather_url).json()
        
        current_weather = weather_response.get("current_weather")
        if current_weather:
            return f"The current weather in {city} is {current_weather['temperature']}°C with wind speed {current_weather['windspeed']} km/h."
        else:
            return f"Could not fetch weather data for {city}."
    except Exception as e:
        return f"Error fetching weather: {str(e)}"

class SimpleGPT:
    def __init__(self):
        load_dotenv()
        self.memory_manager = memoryManager()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY not found in .env file")
            return  
            
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name="qwen/qwen3-32b"
        )
        
        self.tools = [get_weather]
        self.agent = create_react_agent(self.llm, tools=self.tools)
        
        self.system_prompt = "You are a helpful and enthusiastic assistant. You always answer in a friendly tone."
        
    def generate_response(self, user_input):
        msg=self.memory_manager.last10msg()+'\n'+user_input
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=msg)
        ]
        
        # The agent returns a dictionary with the state, including 'messages'
        result = self.agent.invoke({"messages": messages})
        
        # The last message in the list is the final response from the assistant
        last_message = result["messages"][-1]
        self.memory_manager.storeMSG(user_input, last_message.content,last_message.response_metadata)
        return last_message

def main():
    simple_gpt = SimpleGPT()

    print("SimpleGPT initialized with Weather capabilities. Type 'quit' or 'exit' to stop.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
            
        try:
            response = simple_gpt.generate_response(user_input)
            print(f"Bot: {response.content}")
            print("----------------------------------")
            # response.response_metadata might not exist on the message object directly in the same way, 
            # or it might be empty depending on the message type (AIMessage).
            # Let's print it if it exists, otherwise skip to avoid errors.
            if hasattr(response, 'response_metadata'):
                print(f"Metadata: {response.response_metadata}")
        except Exception as e:
            print(f"Error: {e}")

if __name__=="__main__":
    main()