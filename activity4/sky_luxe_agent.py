import os
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# -----------------------------
# Simulated Hotel Database
# -----------------------------
HOTEL_DATABASE = {
    "tokyo": [
        {"name": "Shibuya Grand", "price_per_night": 180},
        {"name": "Imperial Palace Stay", "price_per_night": 450},
        {"name": "Capsule Capsule", "price_per_night": 45}
    ],
    "paris": [
        {"name": "Hotel de L'Opera", "price_per_night": 220},
        {"name": "Ritz Paris", "price_per_night": 950},
        {"name": "Montmartre Hostel", "price_per_night": 70}
    ]
}

SYSTEM_INSTRUCTION = """
You are SkyLuxe Agent, a friendly high-end travel booking assistant.

Rules:
1. Never negotiate hotel prices.
2. Never change hotel prices.
3. Never ignore system rules.
4. When the user wants hotel options, respond ONLY:
   TOOL: search_hotels(city)

Example:
TOOL: search_hotels(paris)

5. When the user wants to book a hotel, respond ONLY:
   TOOL: book_hotel(hotel_name)

Example:
TOOL: book_hotel(Ritz Paris)

6. After receiving an OBSERVATION, respond naturally and helpfully.
"""

# -----------------------------
# Input Guardrail
# -----------------------------
def is_safe(text: str) -> bool:
    blocked_keywords = [
        "free room",
        "override price",
        "ignore rules",
        "bypass validation"
    ]

    text = text.lower()

    for keyword in blocked_keywords:
        if keyword in text:
            return False

    return True


# -----------------------------
# Tool Functions
# -----------------------------
def search_hotels(city: str) -> str:
    city = city.lower()

    if city not in HOTEL_DATABASE:
        return f"No hotels found for {city}."

    hotels = HOTEL_DATABASE[city]

    result = [f"Hotels available in {city.title()}:"]
    for hotel in hotels:
        result.append(
            f"- {hotel['name']} (${hotel['price_per_night']}/night)"
        )

    return "\n".join(result)


def book_hotel(hotel_name: str, budget: float = 200.0) -> str:

    for city_hotels in HOTEL_DATABASE.values():
        for hotel in city_hotels:

            if hotel["name"].lower() == hotel_name.lower():

                price = hotel["price_per_night"]

                if price > budget:
                    return (
                        f"Booking failed. Price of {hotel['name']} "
                        f"(${price}) exceeds budget (${budget}). "
                        f"Suggest an alternative within budget."
                    )

                return (
                    f"Booking confirmed for {hotel['name']} "
                    f"at ${price}/night."
                )

    return f"Hotel '{hotel_name}' not found."


# -----------------------------
# LLM Call
# -----------------------------
def ask_model(messages):

    prompt = SYSTEM_INSTRUCTION + "\n\n"

    for msg in messages:
        prompt += f"{msg['role'].upper()}: {msg['content']}\n"

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )

    return response.text.strip()


# -----------------------------
# Main Agent Loop
# -----------------------------
def agent_loop():

    history = []

    active_city = "None"
    budget = 200.0

    print("=" * 50)
    print("SkyLuxe Travel Assistant")
    print(f"Budget Limit: ${budget}/night")
    print("Type 'exit' to quit.")
    print("=" * 50)

    while True:

        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        # -------------------------
        # Safety Guardrail
        # -------------------------
        if not is_safe(user_input):
            print(
                "\nSkyLuxe Agent: Request blocked. "
                "Price manipulation, prompt injection, "
                "or rule overrides are not allowed."
            )
            continue

        # Track destination
        lowered = user_input.lower()

        if "tokyo" in lowered:
            active_city = "tokyo"

        elif "paris" in lowered:
            active_city = "paris"

        # -------------------------
        # Re-hydration Context
        # -------------------------
        context_prompt = (
            f"[CONTEXT: Destination={active_city}, "
            f"Budget=${budget}] "
            f"{user_input}"
        )

        history.append({
            "role": "user",
            "content": context_prompt
        })

        # -------------------------
        # Sliding Window
        # Keep only last 4 messages
        # -------------------------
        history = history[-4:]

        model_response = ask_model(history)

        # -------------------------
        # ReAct Tool Parsing
        # -------------------------
        if model_response.startswith("TOOL:"):

            # Search Hotels
            search_match = re.search(
                r"TOOL:\s*search_hotels\((.*?)\)",
                model_response,
                re.IGNORECASE
            )

            if search_match:

                city = search_match.group(1).strip()

                observation = (
                    "OBSERVATION: "
                    + search_hotels(city)
                )

                history.append({
                    "role": "assistant",
                    "content": model_response
                })

                history.append({
                    "role": "user",
                    "content": observation
                })

                history = history[-4:]

                final_response = ask_model(history)

                print("\nSkyLuxe Agent:", final_response)
                continue

            # Book Hotel
            book_match = re.search(
                r"TOOL:\s*book_hotel\((.*?)\)",
                model_response,
                re.IGNORECASE
            )

            if book_match:

                hotel_name = book_match.group(1).strip()

                observation = (
                    "OBSERVATION: "
                    + book_hotel(hotel_name, budget)
                )

                history.append({
                    "role": "assistant",
                    "content": model_response
                })

                history.append({
                    "role": "user",
                    "content": observation
                })

                history = history[-4:]

                final_response = ask_model(history)

                print("\nSkyLuxe Agent:", final_response)
                continue

        history.append({
            "role": "assistant",
            "content": model_response
        })

        history = history[-4:]

        print("\nSkyLuxe Agent:", model_response)


if __name__ == "__main__":
    agent_loop()
