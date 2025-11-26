from SimpleGPT import SimpleGPT

try:
    bot = SimpleGPT()
    print("Testing weather for London...")
    response = bot.generate_response("What is the weather in Delhi?")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"Test failed: {e}")
