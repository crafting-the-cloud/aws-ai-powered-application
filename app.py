import os
import requests
import re
from flask import Flask, render_template, request

# Initialize the Flask application
app = Flask(__name__)

# The API endpoint URL
API_URL = "https://xxxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/generate-plan"

def format_career_plan(plan_text):
    """
    Parses the raw string from the API into a structured dictionary
    that's easier to render in the HTML template.
    """
    if not plan_text:
        return None

    # Use a more robust regex to find sections starting with a number and a period.
    # This splits the text into sections like "1. ...", "2. ...", etc.
    sections_raw = re.split(r'\n(?=\d\.\s)', plan_text)
    
    plan = {
        'title': '',
        'sections': [],
        'note': ''
    }

    # The first part is the intro text before the numbered sections
    intro_parts = sections_raw[0].split('\n\n', 1)
    plan['title'] = intro_parts[0].strip()
    
    if len(intro_parts) > 1:
        first_section_text = intro_parts[1]
    else: # Handle cases where there might not be a newline after the title
        first_section_text = ''
        
    # The first section might not have been captured by the split if it's part of the first element
    if first_section_text:
        sections_raw[0] = first_section_text

    # Process each section
    for section_text in sections_raw:
        lines = [line.strip() for line in section_text.strip().split('\n') if line.strip()]
        if not lines:
            continue
            
        heading = lines[0]
        items = [item.lstrip('- ').strip() for item in lines[1:]]
        
        # Check if the last item is the "Note"
        final_note = ''
        if items and items[-1].lower().startswith('note:'):
            final_note = items.pop().lstrip('Note:').strip()
            plan['note'] = final_note

        # --- FIX IS HERE ---
        # Renamed the key from 'items' to 'section_items' to avoid conflict
        # with the built-in dictionary .items() method in Jinja2.
        plan['sections'].append({'heading': heading, 'section_items': items})

    return plan


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Main route to handle the form submission and display the career plan.
    """
    career_plan = None
    error_message = None

    if request.method == 'POST':
        current_role = request.form.get('current_role')
        goal = request.form.get('goal')

        if not current_role or not goal:
            error_message = "Both 'Current Role' and 'Career Goal' are required."
        else:
            payload = {
                "current_role": current_role,
                "goal": goal
            }
            try:
                # --- DEBUGGING ADDED ---
                # Added print statements to log the process to the terminal.
                print("Sending request to API with payload:", payload)
                response = requests.post(API_URL, json=payload, timeout=30)
                print(f"API Response Status Code: {response.status_code}")
                response.raise_for_status()

                api_data = response.json()
                print("API Response JSON:", api_data)

                raw_plan = api_data.get("career_plan")
                print("Extracted Raw Plan Text (first 100 chars):", raw_plan[:100] if raw_plan else "None")
                
                if raw_plan:
                    career_plan = format_career_plan(raw_plan)
                    print("Formatted Career Plan:", career_plan)
                else:
                    error_message = "API returned a valid response, but no career plan was found."
                # --- END DEBUGGING ---

            except requests.exceptions.RequestException as e:
                # Handle network errors, timeouts, etc.
                error_message = f"An error occurred while contacting the API: {e}"
                print(f"ERROR: {error_message}")
            except Exception as e:
                # Handle other potential errors (e.g., JSON parsing)
                error_message = f"An unexpected error occurred: {e}"
                print(f"ERROR: {error_message}")


    return render_template('index.html', career_plan=career_plan, error=error_message)

# To run the app, execute `python app.py` in your terminal
if __name__ == '__main__':
    # Ensure the 'templates' folder exists before running
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("Created 'templates' directory. Please place 'index.html' inside it.")
    
    app.run(debug=True, port=5001)

