import google.generativeai as genai
import os
import json
import re
from ics import Calendar, Event
from datetime import datetime, timedelta
import tempfile # Added for calendar file creation

# --- Agent Class with Long-Term Memory ---

class SousChefAgent:
    def __init__(self, user_id="cli_user", model_name="models/gemini-2.5-flash", memory_file="memory_bank.json"):
        self.user_id = user_id
        self.memory_file = memory_file
        
        # --- API Key Configuration ---
        # It's crucial to set GEMINI_API_KEY as an environment variable for production.
        # Fallback for testing purposes if not set.
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set. Please provide a valid API key.")
        
        genai.configure(api_key=self.api_key)
        
        # --- Tool Definitions ---
        # This dictionary defines the tools the agent can use. Each tool has a description
        # and parameters, helping the LLM understand when and how to use it.
        self.tools = {
            "add_to_pantry": {
                "description": "Add a list of ingredients to the user's pantry. Expects a JSON object with an 'ingredients' key, which is a list of strings.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ingredients": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A list of ingredients to add."
                        }
                    },
                    "required": ["ingredients"]
                }
            },
            "remove_from_pantry": {
                "description": "Remove a list of ingredients from the user's pantry. Expects a JSON object with an 'ingredients' key, which is a list of strings.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ingredients": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A list of ingredients to remove."
                        }
                    },
                    "required": ["ingredients"]
                }
            },
            "add_feedback": {
                "description": "Add user feedback for a recipe. Expects a JSON object with 'recipe_name' (string) and 'feedback' (string: 'like' or 'dislike').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipe_name": {"type": "string", "description": "The name of the recipe."},
                        "feedback": {"type": "string", "enum": ["like", "dislike"], "description": "The feedback ('like' or 'dislike')."}
                    },
                    "required": ["recipe_name", "feedback"]
                }
            },
            "view_pantry": {
                "description": "View the current contents of the user's pantry. Does not require any parameters.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            "generate_meal_plan": {
                "description": "Generates a meal plan based on specified days, diet, and preferences. Returns a JSON object with a 'plan' key.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Number of days for the meal plan (e.g., 3)."},
                        "diet": {"type": "string", "description": "Dietary restrictions (e.g., 'vegetarian', 'vegan')."},
                        "preferences": {"type": "string", "description": "General meal preferences (e.g., 'quick meals', 'high protein')."}
                    }
                }
            },
            "generate_recipe": {
                "description": "Generates a recipe based on pantry items, extra ingredients, dietary needs, and cooking time. Returns a JSON object with recipe details.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "extra_ingredients": {"type": "string", "description": "Additional ingredients to include (e.g., 'chicken, bell peppers')."},
                        "dietary_needs": {"type": "string", "description": "Specific dietary requirements (e.g., 'gluten-free', 'low-carb')."},
                        "cooking_time": {"type": "string", "description": "Maximum cooking time (e.g., '30 minutes')."}
                    }
                }
            },
            "create_calendar_file": {
                "description": "Creates an .ics calendar file from a generated meal plan. Expects a JSON array of meal objects.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "meal_plan": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "day": {"type": "integer", "description": "Day number in the plan."},
                                    "meal_type": {"type": "string", "description": "Type of meal (e.g., 'Breakfast', 'Lunch', 'Dinner')."},
                                    "meal_name": {"type": "string", "description": "Name of the meal."}
                                },
                                "required": ["day", "meal_type", "meal_name"]
                            },
                            "description": "A list of meal objects representing the meal plan."
                        }
                    },
                    "required": ["meal_plan"]
                }
            }
        }

        # --- System Instruction ---
        # The system instruction now guides the LLM to use the defined tools by returning
        # a specific JSON structure for tool calls.
        self.system_instruction = f"""
        You are the AI Sous-Chef, a friendly and expert kitchen assistant. 
        Your primary goal is to help users with meal planning, recipe generation, and pantry management.
        You are an expert in cooking, nutrition, and meal planning.

        You have access to the following tools:
        {json.dumps(self.tools, indent=4)}

        When you need to use a tool, respond with a JSON object containing two fields:
        - "tool_code": The name of the tool to use (e.g., "add_to_pantry").
        - "tool_params": A JSON object containing the parameters for the tool.

        If you are not using a tool, respond conversationally to the user.
        Do not add any conversational text or markdown formatting outside of the JSON structure when using a tool.
        """
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=self.system_instruction
        )
        self.conversation = self.model.start_chat(history=[])
        
        # --- Memory Initialization ---
        self.pantry = set()
        self.liked_recipes = set()
        self.disliked_recipes = set()
        self._load_memory()

    def _load_memory(self):
        """
        Loads the user's data from the memory file. This includes pantry items,
        liked, and disliked recipes, providing the agent with long-term memory.
        """
        if not os.path.exists(self.memory_file):
            return # File doesn't exist, will be created on first save

        with open(self.memory_file, 'r') as f:
            try:
                full_memory_bank = json.load(f)
                user_data = full_memory_bank.get(self.user_id, {})
                self.pantry = set(user_data.get('pantry', []))
                self.liked_recipes = set(user_data.get('liked_recipes', []))
                self.disliked_recipes = set(user_data.get('disliked_recipes', []))
            except json.JSONDecodeError:
                # If the file is corrupt or empty, it will be overwritten on save.
                # This ensures robustness against malformed memory files.
                pass 

    def _save_memory(self):
        """
        Saves the current user's data (pantry, liked/disliked recipes) to the
        memory file, ensuring persistence across sessions.
        """
        full_memory_bank = {}
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                try:
                    full_memory_bank = json.load(f)
                except json.JSONDecodeError:
                    pass # Overwrite if corrupt

        full_memory_bank[self.user_id] = {
            'pantry': list(self.pantry),
            'liked_recipes': list(self.liked_recipes),
            'disliked_recipes': list(self.disliked_recipes)
        }

        with open(self.memory_file, 'w') as f:
            json.dump(full_memory_bank, f, indent=4)

    def view_pantry(self):
        """Returns the current contents of the pantry."""
        if not self.pantry:
            return {"pantry": []}
        return {"pantry": sorted(list(self.pantry))}

    def _call_tool(self, tool_code, tool_params):
        """
        Dispatches and executes the appropriate tool function based on the LLM's
        tool call. This is the 'Act' part of the agent's Think-Act cycle.
        """
        if tool_code == "add_to_pantry":
            # Tool: Add ingredients to the user's pantry
            self.add_to_pantry(tool_params["ingredients"])
            return {"status": "success", "message": f"Added {tool_params['ingredients']} to pantry."}
        elif tool_code == "remove_from_pantry":
            # Tool: Remove ingredients from the user's pantry
            self.remove_from_pantry(tool_params["ingredients"])
            return {"status": "success", "message": f"Removed {tool_params['ingredients']} from pantry."}
        elif tool_code == "add_feedback":
            # Tool: Record user feedback for a recipe
            self.add_feedback(tool_params["recipe_name"], tool_params["feedback"])
            return {"status": "success", "message": f"Feedback for '{tool_params['recipe_name']}' received."}
        elif tool_code == "view_pantry":
            # Tool: Display current pantry contents
            return self.view_pantry()
        elif tool_code == "generate_meal_plan":
            # Tool: Generate a meal plan based on preferences
            return self.generate_meal_plan(**tool_params)
        elif tool_code == "generate_recipe":
            # Tool: Generate a recipe based on pantry and preferences
            return self.generate_recipe(**tool_params)
        elif tool_code == "create_calendar_file":
            # Tool: Create an ICS calendar file from a meal plan
            return self.create_calendar_file(tool_params["meal_plan"])
        else:
            return {"status": "error", "message": f"Unknown tool: {tool_code}"}

    def ask(self, prompt):
        """
        Sends a prompt to the AI, handles tool calls, and returns a response.
        This method embodies the 'Think' part of the agent's Think-Act cycle.
        """
        try:
            response = self.conversation.send_message(prompt)
            raw_text = response.text

            # Use regex to find a JSON object in the response
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)

            if json_match:
                json_string = json_match.group(0)
                try:
                    json_response = json.loads(json_string)
                    # If it's a valid tool call, execute it
                    if "tool_code" in json_response and "tool_params" in json_response:
                        return self._call_tool(json_response["tool_code"], json_response["tool_params"])
                    else:
                        # It's a valid JSON response, but not a tool call (e.g., a recipe)
                        return json_response
                except json.JSONDecodeError:
                    # Found something that looked like JSON, but it was invalid.
                    # Fall through to treat the entire text as a conversational response.
                    pass
            
            # If no JSON was found or parsing failed, treat the whole thing as a conversation
            cleaned_text = raw_text.strip().replace("```json", "").replace("```", "")
            return {"response": cleaned_text}

        except Exception as e:
            # General error during AI interaction
            return {"error": f"Failed to get response from model: {e}", "raw_response": response.text if 'response' in locals() else "No response from model."}

    def add_to_pantry(self, ingredients):
        """Adds a list of ingredients to the pantry and saves memory."""
        self.pantry.update([item.strip().lower() for item in ingredients])
        self._save_memory()

    def remove_from_pantry(self, ingredients):
        """Removes a list of ingredients from the pantry and saves memory."""
        for item in ingredients:
            self.pantry.discard(item.strip().lower())
        self._save_memory()
        
    def add_feedback(self, recipe_name, feedback):
        """Adds feedback for a recipe and saves memory."""
        recipe_name = recipe_name.strip().lower()
        if feedback.lower() == 'like':
            self.liked_recipes.add(recipe_name)
            self.disliked_recipes.discard(recipe_name)
        elif feedback.lower() == 'dislike':
            self.disliked_recipes.add(recipe_name)
            self.liked_recipes.discard(recipe_name)
        self._save_memory()

    def generate_meal_plan(self, days=3, diet='any', preferences=''):
        """Generates a meal plan in a structured JSON format."""
        prompt = f"""
        Please create a meal plan for {days} days with the following preferences:
        - Dietary Restrictions: {diet}
        - General Preferences: {preferences}

        You must respond with only a single JSON object. Do not include any text, conversational filler, or markdown formatting before or after the JSON object.
        The JSON object should have a single key "plan", which is an array of meal objects.
        Each meal object must have the following keys: "day" (integer), "meal_type" (string: "Breakfast", "Lunch", or "Dinner"), and "meal_name" (string).

        Example format:
        {{
          "plan": [
            {{ "day": 1, "meal_type": "Breakfast", "meal_name": "Oatmeal with Berries" }},
            {{ "day": 1, "meal_type": "Lunch", "meal_name": "Quinoa Salad" }}
          ]
        }}
        """
        # Call the underlying LLM with a prompt specifically designed to get JSON
        response_json = self.ask(prompt) 
        return response_json

    def generate_recipe(self, extra_ingredients='', dietary_needs='', cooking_time=''):
        """Generates a recipe in a structured JSON format based on pantry and preferences."""
        pantry_items = ", ".join(self.pantry)
        liked_prompt = f"The user likes these recipes: {', '.join(self.liked_recipes)}. Draw inspiration from them." if self.liked_recipes else ''
        disliked_prompt = f"The user dislikes these recipes: {', '.join(self.disliked_recipes)}. Do not suggest them." if self.disliked_recipes else ''

        prompt = f"""
        Please suggest a recipe. You must respond with only a single JSON object.
        
        The JSON object should contain the following keys: "title", "description", "servings", "prep_time", "cook_time", "ingredients" (an array of strings), and "instructions" (an array of strings).
        
        IMPORTANT: The "title" should be a fun and creative name for the recipe.

        Base the recipe on the following context:
        - My pantry contains: {pantry_items}
        - Additional ingredients I have: {extra_ingredients}
        - Dietary Needs: {dietary_needs}
        - Max Cooking Time: {cooking_time}
        - {liked_prompt}
        - {disliked_prompt}
        
        Example format:
        {{
          "title": "Zesty Chicken & Broccoli Power Bowl",
          "description": "A quick and easy stir-fry with a spicy kick.",
          "servings": "2",
          "prep_time": "10 minutes",
          "cook_time": "15 minutes",
          "ingredients": [
            "1 lb chicken breast, cut into bite-sized pieces",
            "1 tbsp soy sauce",
            "1 cup broccoli florets"
          ],
          "instructions": [
            "Heat oil in a large skillet or wok.",
            "Add chicken and cook until browned.",
            "Add broccoli and stir-fry for 3-5 minutes."
          ]
        }}
        """
        print()
        response_json = self.ask(prompt)
        return response_json

    def create_calendar_file(self, meal_plan):
        """
        Creates an .ics calendar file from a meal plan JSON object and saves it to a temporary location.
        """
        try:
            c = Calendar()
            for meal in meal_plan:
                e = Event()
                e.name = f"{meal['meal_type']}: {meal['meal_name']}"
                
                # Use a placeholder date if parsing fails, but the AI should provide it
                try:
                    meal_date = datetime.strptime(meal.get('day_str', str(datetime.now().date())), '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    meal_date = datetime.now().date() + timedelta(days=int(meal.get('day', 1)) - 1)


                if meal['meal_type'].lower() == 'breakfast':
                    event_time = datetime.combine(meal_date, datetime.min.time()) + timedelta(hours=8)
                elif meal['meal_type'].lower() == 'lunch':
                    event_time = datetime.combine(meal_date, datetime.min.time()) + timedelta(hours=13)
                else: # Dinner
                    event_time = datetime.combine(meal_date, datetime.min.time()) + timedelta(hours=19)
                
                e.begin = event_time
                e.duration = timedelta(hours=1)
                c.events.add(e)

            # Save to a temporary, publicly accessible directory
            calendar_dir = os.path.join(tempfile.gettempdir(), 'sous_chef_calendars')
            os.makedirs(calendar_dir, exist_ok=True)
            file_path = os.path.join(calendar_dir, f'{self.user_id}_meal_plan.ics') # Unique filename per user

            with open(file_path, 'w') as f:
                f.writelines(c)
            
            return {
                "status": "success",
                "message": "Calendar file created successfully.",
                "file_path": file_path
            }

        except Exception as e:
            return {"status": "error", "message": f"Failed to create calendar file: {e}"}


if __name__ == '__main__':
    print("Welcome to AI Sous-Chef CLI Agent!")
    print("Type 'exit' or 'quit' to end the session.")

    agent = SousChefAgent(user_id="cli_user")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            # Save memory before exiting
            agent._save_memory()
            print("Session ended. Goodbye!")
            break

        # Here, we will eventually implement the Think-Act cycle.
        # For now, it's a direct pass-through to the agent's ask method.
        # This will be refined as we implement tool use.
        response = agent.ask(user_input)

        if isinstance(response, dict):
            if "error" in response:
                print(f"Agent Error: {response['error']}")
                if "raw_response" in response and response['raw_response'] != "No response from model.":
                    print(f"Raw LLM Response: {response['raw_response']}")
            elif "response" in response: # Conversational response
                print("Agent:", response["response"])
            elif "status" in response and response["status"] == "success":
                # Tool execution successful, display message or specific output
                print(f"Agent: {response['message']}")
                if "pantry" in response:
                    print("Current Pantry:", ", ".join(response["pantry"]))
                if "file_path" in response:
                    print(f"Calendar saved to: {response['file_path']}")
            elif "plan" in response: # Meal plan response
                print("Agent (Meal Plan):")
                for meal in response["plan"]:
                    print(f"  Day {meal['day']}: {meal['meal_type']} - {meal['meal_name']}")
            elif "title" in response and "ingredients" in response: # Recipe response
                print(f"Agent (Recipe): {response['title']}")
                print(f"  Description: {response['description']}")
                print(f"  Servings: {response['servings']}")
                print(f"  Prep Time: {response['prep_time']}")
                print(f"  Cook Time: {response['cook_time']}")
                print("  Ingredients:")
                for ingredient in response["ingredients"]:
                    print(f"    - {ingredient}")
                print("  Instructions:")
                for step in response["instructions"]:
                    print(f"    - {step}")
            else:
                print("Agent (Unhandled structured response):", response)
        else:
            print("Agent (Raw response):", response)
