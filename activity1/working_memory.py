import os
from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in .env file!")

client = genai.Client(api_key=api_key)

history = []

# def agent_loop(user_input):
#     global history
    
chat = client.chats.create(
        model = 'gemini-3.1-flash-lite',
#         history = history
     )
    
#     response = chat.send_message(user_input)
    
#     history = chat.history
    
#     return response.text


# print(f"Turn 1: {agent_loop('Hi, my name is Ricardo')}")

# print(f"Turn 2: {agent_loop('Create an acrostic for my name')}")

def agent_loop(user_input):
    response = chat.send_message(user_input)
    return response.text 



def main():
    print("\n--- Agent is active. Type 'exit' to quit. ---")
    while True:
        try:
            user_msg = input("\nUser:")
            if user_msg.lower() == 'exit':
                print("Agent is quitting. Goodbye...")
                break
            
            if not user_msg.strip():
                continue
            
            response = agent_loop(user_msg)
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            print("\nSession interruped. Exiting...")
            break;
        
if __name__ == "__main__":
    main()