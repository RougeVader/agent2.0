<div align="center">

<pre>
   ___    ____         _________              __  _              
  / _ |  / / /________/ / __/ __/__  ___ ___ _/ /_(_)__  ___  ___ 
 / __ | / / /__/___/ / _// _// _ \/ -_) _ `/ __/ / _ \/ -_) -_)
/_/ |_|/_/\   / /_/ /___/___/_//_/\__/_/\_,_/\__/_/\___/\__/
                                                               
</pre>

**AI Sous-Chef: Your Personal AI Kitchen Assistant**

</div>

<div align="center">

[![Python Version][python-shield]](#)
[![License: MIT][license-shield]](LICENSE.md)
[![Pull Requests Welcome][pr-shield]](#contributing)

</div>

An intelligent, conversational CLI agent built with Google's Gemini LLM that revolutionizes home cooking by making meal planning, recipe discovery, and pantry management effortless and personal.

---

## Overview

The AI Sous-Chef is a Python-based agent that acts as a smart kitchen assistant. It leverages a Large Language Model (LLM) to understand natural language commands, manage a persistent pantry, and generate personalized meal plans and recipes. The agent is designed with a tool-based architecture, allowing for easy extension and integration of new capabilities.

This project serves as a powerful demonstration of modern agentic AI systems, including long-term memory management and dynamic tool use.

## Demo

Here is a sample interaction with the AI Sous-Chef:

```
Welcome to AI Sous-Chef CLI Agent!
Type 'exit' or 'quit' to end the session.

You: Hello! I just got back from the store. I have chicken breast, a head of broccoli, and some white rice.
Agent: Added ['chicken breast', 'broccoli', 'white rice'] to pantry.

You: What's in my pantry right now?
Agent: Current Pantry: broccoli, chicken breast, white rice

You: That's right. Can you suggest a simple recipe using those ingredients? I only have about 30 minutes.
Agent (Recipe): Simple Lemon-Herb Chicken and Broccoli
  Description: A quick, healthy, and delicious one-pan meal perfect for a weeknight.
  Servings: 2
  Prep Time: 5 minutes
  Cook Time: 20 minutes
  Ingredients:
    - 1 lb chicken breast, cut into bite-sized pieces
    - 1 head of broccoli, cut into florets
    - 1 cup white rice
    - 1 lemon, juiced
    - 2 tbsp olive oil
    - 1 tsp dried oregano
    - Salt and pepper to taste
  Instructions:
    - Cook the white rice according to package directions.
    - While the rice cooks, toss the chicken and broccoli with olive oil, lemon juice, oregano, salt, and pepper.
    - Heat a large skillet over medium-high heat. Add the chicken and broccoli mixture.
    - Cook for 15-20 minutes, stirring occasionally, until the chicken is cooked through and the broccoli is tender-crisp.
    - Serve the chicken and broccoli over the cooked rice.

You: I loved that recipe!
Agent: Feedback for 'simple lemon-herb chicken and broccoli' received.

You: exit
Session ended. Goodbye!
```

## Features

-   **Conversational Interface:** Interact naturally via a simple command-line interface.
-   **Smart Pantry Management:** The agent maintains a persistent state of your pantry across sessions.
-   **Intelligent Recipe Generation:** Get recipes tailored to your available ingredients, dietary needs, and time constraints.
-   **Personalized Meal Planning:** Generate multi-day meal plans and export them to a calendar file (`.ics`).
-   **Long-Term Memory:** The agent remembers your liked and disliked recipes to personalize future suggestions.
-   **Tool-Based Architecture:** The agent uses a set of defined "tools" to perform actions, making the system modular and extensible.

## Architecture

The agent operates on an "Observe-Think-Act" loop, using the Gemini LLM to reason and decide which tool to use based on the user's prompt.

<div align="center">

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
</div>

## Getting Started

### Prerequisites

-   Python 3.8+
-   An active Google Gemini API Key. You can get one at [Google AI Studio](https://aistudio.google.com/app/apikey).

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Install Dependencies

It's recommended to use a virtual environment.

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install required packages
pip install -r requirements.txt
```
*(Note: You may need to create a `requirements.txt` file from the existing dependencies if it's not already present).*


### 3. Set Your API Key

The application requires your Google Gemini API key to be set as an environment variable.

-   **Windows (PowerShell):** `$env:GEMINI_API_KEY="YOUR_API_KEY"`
-   **macOS/Linux:** `export GEMINI_API_KEY='YOUR_API_KEY'`

*(Replace `YOUR_API_KEY` with your actual key).*

### 4. Run the Agent

Start the interactive CLI agent:

```bash
python main.py
```

## Deployment

This agent is designed to be deployed as a containerized application, for example, on Google Cloud Run. The included `Dockerfile` allows for easy image building.

### 1. Build the Docker Image

From the root of the project directory, run the following command to build the Docker image:

```bash
docker build -t ai-sous-chef .
```

### 2. Run the Container Locally (Optional)

To test the container on your local machine, run it in interactive mode:

```bash
# Don't forget to pass your API key as an environment variable
docker run -it -e GEMINI_API_KEY="YOUR_API_KEY" ai-sous-chef
```

### 3. Deploy to Google Cloud Run

To deploy the agent as a continuously running service, you can use Google Cloud Run.

**Prerequisites:**
-   Google Cloud SDK (`gcloud`) installed and configured.
-   Enable the Artifact Registry and Cloud Run APIs in your GCP project.

**Steps:**

```bash
# 1. Configure Docker to authenticate with Google Cloud Artifact Registry
gcloud auth configure-docker

# 2. Define environment variables for convenience
export PROJECT_ID="your-gcp-project-id"
export REGION="your-gcp-region" # e.g., us-central1
export IMAGE_NAME="ai-sous-chef"
export IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${IMAGE_NAME}"

# 3. Build and push the image to Google Artifact Registry
docker build -t ${IMAGE_TAG} .
docker push ${IMAGE_TAG}

# 4. Deploy to Cloud Run, passing the Gemini API key as a secret
# (It's recommended to use Secret Manager for your API key)
gcloud run deploy ${IMAGE_NAME} \
  --image ${IMAGE_TAG} \
  --region ${REGION} \
  --set-secrets="GEMINI_API_KEY=your-secret-name:latest" \
  --no-allow-unauthenticated
```
*Note: The CLI agent runs in an interactive loop. For a non-interactive deployment (e.g., as a backend for a web app), you would need to adapt `main.py` to handle requests differently (e.g., via an API framework like Flask or FastAPI).*

## Contributing

Contributions are welcome! Whether it's reporting a bug, suggesting a new feature, or submitting a pull request, we appreciate your help.

### How to Contribute

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** to your local machine.
3.  **Create a new branch** for your feature or bug fix (`git checkout -b feature/your-feature-name`).
4.  **Make your changes** and commit them with a clear, descriptive commit message.
5.  **Push your changes** to your fork on GitHub (`git push origin feature/your-feature-name`).
6.  **Open a Pull Request** to the `main` branch of the original repository.

### Reporting Bugs

Please open an issue on GitHub and include:
- A clear, descriptive title.
- Steps to reproduce the bug.
- The expected behavior and what actually happened.
- Your operating system and Python version.

## Roadmap

This project has a strong foundation. Future enhancements could include:

-   [ ] **External API Tools:** Integrate with grocery delivery APIs or nutritional databases.
-   [ ] **Proactive Suggestions:** Allow the agent to make suggestions based on timers or pantry item expiry.
-   [ ] **Multi-Modal Input:** Enable users to provide images of their pantry for automatic ingredient detection.
-   [ ] **Web Interface:** Build a dedicated web UI to interact with the agent backend.

## License

This project is licensed under the MIT License. See the [LICENSE.md](LICENSE.md) file for details.

<!-- Markdown Shields -->
[python-shield]: https://img.shields.io/badge/Python-3.8+-blue.svg
[license-shield]: https://img.shields.io/badge/License-MIT-green.svg
[pr-shield]: https://img.shields.io/badge/Pull_Requests-Welcome-brightgreen.svg
