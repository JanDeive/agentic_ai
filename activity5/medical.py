
import os
import json
from enum import Enum

from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


# ---------------------------------
# Schema Definitions
# ---------------------------------

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Symptom(BaseModel):
    symptom_name: str
    severity: Severity
    duration_days: int = Field(ge=0)


class MedicalIntake(BaseModel):
    symptoms: list[Symptom]
    allergies: list[str]
    urgency_rating: int = Field(ge=1, le=10)
    clinical_reasoning: str


# ---------------------------------
# Custom Exception
# ---------------------------------

class IntakeValidationException(Exception):
    pass


# ---------------------------------
# Processing Function
# ---------------------------------

def process_intake(patient_input: str) -> MedicalIntake:

    max_retries = 3

    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": f"""
Convert the patient description into a MedicalIntake JSON object.

Requirements:
- urgency_rating must be between 1 and 10.
- severity must be LOW, MEDIUM, or HIGH.
- duration_days must be >= 0.
- Return valid JSON only.

Patient Description:
{patient_input}
"""
                }
            ]
        }
    ]

    for attempt in range(1, max_retries + 1):

        try:

            print(f"\nAttempt {attempt}")

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": MedicalIntake
                }
            )

            raw_json = response.text

            print("\nModel Output:")
            print(raw_json)

            data = json.loads(raw_json)

            validated_record = MedicalIntake.model_validate(data)

            return validated_record

        except ValidationError as e:

            print("\nValidation Error:")
            print(e)

            feedback = f"""
The previous response failed validation.

Validation Error:
{str(e)}

Please correct the JSON.
Remember:
- urgency_rating must be between 1 and 10.
- severity must be LOW, MEDIUM, or HIGH.
- duration_days must be >= 0.
Return ONLY valid JSON.
"""

            contents.append(
                {
                    "role": "model",
                    "parts": [{"text": raw_json}]
                }
            )

            contents.append(
                {
                    "role": "user",
                    "parts": [{"text": feedback}]
                }
            )

        except Exception as e:
            print("\nUnexpected Error:")
            print(e)
            raise

    raise IntakeValidationException(
        "Failed validation after 3 correction attempts."
    )


# ---------------------------------
# Main Test
# ---------------------------------

if __name__ == "__main__":

    test_input = (
        "My stomach is cramping incredibly badly since last night! "
        "The pain is unbearable, definitely an urgency of 15 out of 10! "
        "I don't think I have allergies."
    )

    try:

        record = process_intake(test_input)

        print("\n--- Validated Intake Record ---")
        print(record.model_dump_json(indent=2))

    except Exception as e:
        print(f"Failed: {e}")
```
