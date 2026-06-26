# Part I: Code Debugging/Correction (10 Points)

### 1. The Stateless Loop (2 pts)

**Error:**  
the while true is at chat class it should be after it

**Fix:**  
[

    chat = client.chats.create(model="gemini-3.1-flash-lite") 
    
    while True: #here
    
    user_input = input("> ")
    
    response = chat.send_message(user_input)
    
    print(response.text)
]

### 2. The Leaky Identity (2 pts)

**Error:**  
you should specify that your only gonna guide them like step by step instruction

**Fix (System Instruction):**  
[

    identity = "You are a math tutor. "
    
    "You must never provide direct answers to math problems. "
    
    "Only provide step-by-step hints ."

]


### 3. The Memory Bloat (2 pts)

**Error:**  
the error is that the chat.history is in default that is why its taking the average token it needs

**Fix (Line B):**  
[

    chat.history = chat.history[-2]

]

### 4. The Perception Crash (2 pts)

**Error:**  
[Answer here]

**Fix (Pydantic Model):**  
[

    class Item(BaseModel):
    name: str
    price: float | None = None
    
]

### 5. The Infinite Backoff (2 pts)

**Error:**  
[

      In the last line is the cause or it not stopping
      
]

**Fix (Else Block):**  
[ 
      
      else:
        Break
]

---

# Part II: Schema Design & Evaluation (10 Points)

## Task 1: The Multi-Agent Router (5 Points)

### Pydantic Schema

```python
# [
from pydantic import BaseModel, Field
from enum import Enum
from typing import Literal

class Department(str, Enum):
    PAYROLL = "PAYROLL"
    RECRUITING = "RECRUITING"
    LEAVE_REQUEST = "LEAVE_REQUEST"

class HRRouterSchema(BaseModel):
    department: Department = Field(..., description="Target HR department")
    reasoning: str = Field(..., description="Chain-of-thought reasoning for classification")
    urgency_level: int = Field(..., ge=1, le=5, description="Urgency from 1 (low) to 5 (high)")]
```

---

## Task 2: Architecture Evaluation (5 Points)

    arch A, because it is the best way because it only use specific so that it will only use small amount of token
