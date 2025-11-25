# AI Sous-Chef CLI Agent

## Project Overview

This project implements an **AI Sous-Chef CLI Agent**, a conversational concierge agent designed to act as a personal kitchen assistant accessible directly from your command line. It streamlines meal planning, recipe generation, and shopping list creation, aiming to reduce food waste and decision fatigue in the kitchen.

This agent demonstrates key concepts of building intelligent agents, including tool use, persistent memory, and observable decision-making, as taught in the Capstone course.

## Features & Implemented Concepts

This project directly demonstrates the following key concepts from the course curriculum:

1.  **Agent powered by an LLM:** The core of the Sous-Chef is driven by the Google Gemini model, which processes user requests, makes decisions, and generates responses.
2.  **Tools (Custom Tools):** The agent is equipped with a suite of custom-built tools that allow it to interact with its environment (your pantry, calendar) and perform specific actions (generate recipes, meal plans).
3.  **Sessions & Memory (Long-Term Memory):** The agent maintains a persistent memory using `memory_bank.json`. It remembers your pantry items, liked, and disliked recipes across sessions, providing a personalized experience.
4.  **Loop Agents:** The agent operates in a continuous "Observe-Think-Act" loop within the command line, allowing for an interactive and stateful conversation.
5.  **Observability:** The agent's decision-making process is made transparent through verbose logging (`[THINKING]`) that shows when it decides to use a tool and with what parameters.

## Problem, Solution, and Value Proposition (The Pitch)

**Problem:** The modern kitchen is chaotic. Juggling recipes, managing ingredients, and deciding "what's for dinner" leads to decision fatigue and food waste. Users often struggle to utilize ingredients they already have, leading to repetitive meals or forgotten items.

**Solution:** The **AI Sous-Chef CLI Agent** acts as a personal, intelligent assistant that lives in your terminal. It provides on-demand meal planning, recipe suggestions tailored to your current pantry and preferences, and helps you keep track of what you have. By leveraging agentic principles, it automates decision-making processes that typically consume time and mental effort.

**Value Proposition:** The agent saves time and reduces mental load by streamlining kitchen tasks. It minimizes food waste by encouraging the use of existing ingredients. Its personalized memory learns from your feedback, offering increasingly relevant and satisfying culinary experiences. The clear observability allows users to understand and trust the agent's decisions.

## Architecture

The AI Sous-Chef CLI Agent follows a classic agentic architecture based on the "Observe-Think-Act" loop:

```
+------------------+     +---------------------+
|   User Input     |     |   SousChefAgent     |
|   (CLI)          |---> | (Python Script)     |
+------------------+     +----------|----------+
                             |  Observe & Think |
                             v                  ^
                  +---------------------+      |
                  | LLM (Google Gemini) |      |
                  +----------|----------+      |
                             |                  |
                             v                  | (LLM Response:
                  +---------------------+      |  Tool Call or Text)
                  |    Tool Dispatcher  |      |
                  +----------|----------+      |
                             v                  |
                  +---------------------+      |
                  |     Agent Tools     | -----+
                  |  - Pantry Management|
                  |  - Meal Plan Gen.   |
                  |  - Recipe Gen.      |
                  |  - Calendar Export  |
                  +----------|----------+
                             |
                             v
                  +------------------+
                  |  Memory Bank     |
                  | (memory_bank.json)|
                  +------------------+
```

1.  **User Input (Observe):** The agent continuously prompts the user for commands or questions via the CLI.
2.  **SousChefAgent (Think):** The user's input, along with the agent's current memory (pantry, preferences), is sent to the LLM. The LLM then "thinks" about the request and decides if a tool is needed or if a conversational response is appropriate.
3.  **LLM (Google Gemini):** The generative model processes the input and system instructions. If a tool is required, it outputs a structured JSON object specifying the `tool_code` and `tool_params`. Otherwise, it generates a conversational text response.
4.  **Tool Dispatcher (Act):** The agent parses the LLM's response. If it's a tool call, the dispatcher executes the corresponding Python function (tool) with the provided parameters.
5.  **Agent Tools (Act):** These are Python functions that perform specific tasks, such as modifying the pantry, querying the LLM for a meal plan, generating a recipe, or creating an `.ics` calendar file.
6.  **Memory Bank:** A `memory_bank.json` file is used for long-term persistence of user-specific data, including pantry contents and recipe feedback.

## Setup and Installation

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)

### 1. Navigate to the Agent Directory

Open your terminal or command prompt and navigate to the `agent2.0` directory:

```bash
cd agent2.0
```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install -q -U google-generativeai Flask-Cors ics
```
*(Note: Flask-Cors is listed in the original requirements, though technically not strictly needed for a pure CLI agent, it's included for consistency with the initial project setup if a web component were ever re-added.)*

### 3. Set Your Gemini API Key

This project requires a Google Gemini API key.

1.  Go to the [Google AI Studio](https://aistudio.google.com/app/apikey) to create your API key.
2.  **Set an Environment Variable:** For the application to work securely, you must set an environment variable named `GEMINI_API_KEY`.
    *   **Windows (Command Prompt):** `set GEMINI_API_KEY=YOUR_API_KEY`
    *   **Windows (PowerShell):** `$env:GEMINI_API_KEY="YOUR_API_KEY"`
    *   **macOS/Linux:** `export GEMINI_API_KEY=YOUR_API_KEY`
    (Replace `YOUR_API_KEY` with your actual key).

*Note: For quick testing, the agent contains a fallback key, but using an environment variable is strongly recommended.*

### 4. Run the Agent

Execute the Python script from your terminal:

```bash
python main.py
```

### 5. Interact with the Agent

Once running, you can type your requests and commands directly into the terminal. Observe the `[THINKING]` logs to see the agent's decision-making process.

**Example Interactions:**

*   `Hello Sous-Chef, what's in my pantry?` (Expects `view_pantry` tool call)
*   `I have chicken, broccoli, and rice.` (Expects `add_to_pantry` tool call)
*   `Suggest a recipe using chicken and broccoli.` (Expects `generate_recipe` tool call)
*   `Remove rice from my pantry.` (Expects `remove_from_pantry` tool call)
*   `Create a 3-day vegetarian meal plan.` (Expects `generate_meal_plan` tool call)
*   `I liked the "Spicy Chicken Stir-Fry" recipe.` (Expects `add_feedback` tool call)

Type `exit` or `quit` to end the session. Your pantry and feedback will be saved automatically.

## Project Journey & Future Enhancements

The project began as a Flask web application, but to fully embrace and demonstrate the core agentic concepts, it was refactored into a Command-Line Interface (CLI) agent. This transition allowed for a deeper focus on the agent's internal "Think-Act" loop, tool use, and state management.

**Future Enhancements:**

*   **Advanced Tooling:** Integrate external APIs (e.g., grocery delivery services, nutritional databases) as new tools.
*   **Multi-Agent Systems:** Implement a system where different agents collaborate on complex tasks (e.g., a "Planning Agent" and a "Shopping Agent").
*   **Natural Language Parameter Extraction:** Improve the LLM's ability to extract tool parameters more reliably from less structured user input.
*   **Event-Driven Interactions:** Move beyond simple request-response to a more event-driven model where the agent can proactively offer suggestions.
*   **Web-based Agent UI:** Develop a new, dedicated web interface designed specifically to interact with this CLI agent's input/output, offering a more user-friendly experience without sacrificing the agent's core principles.
