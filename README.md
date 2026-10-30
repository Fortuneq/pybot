# pybot — AI meal-plan API

A small Flask service that generates a one-day meal plan tailored to the user — sex, height, weight, goal, number of meals, dietary restrictions, allergies, cooking time and budget — using an LLM through the g4f client. The response includes total calories, cost and cooking time.

## API

`POST /generate` with the user's parameters (JSON) → a generated daily meal plan.

Requests are rate-limited (one per second) and processed under a lock to keep the upstream provider happy.

## Run

```bash
pip install flask g4f
python main.py
```

## Stack

Python, Flask, g4f.
