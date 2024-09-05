from flask import Flask, render_template, request, jsonify
import pandas as pd
from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer
import re

app = Flask(__name__)

# Load the Excel file for faculty info
data = pd.read_excel('Faculty.xlsx')

# Load the CSV file for admission info and filter out empty rows
admission_data = pd.read_csv('admissions.csv', encoding='ISO-8859-1').dropna(subset=['Process'])

# Load the GPT-2 model and tokenizer
model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

# Initialize the text generation pipeline
generator = pipeline('text-generation', model=model, tokenizer=tokenizer)

def generate_ai_response(user_message):
    """Generate a response using GPT-2 AI model."""
    response = generator(user_message, max_length=50, num_return_sequences=1)[0]['generated_text']
    return response.strip()

def get_admission_info():
    """Fetch the admission-related information from the CSV file."""
    return '\n'.join(admission_data['Process'].tolist())  # Join all instructions into a single response

def normalize_query(user_message):
    """Normalize the input to focus on the core query, e.g., a name."""
    user_message = user_message.lower()
    
    # Remove common phrases to focus on the name
    patterns = [
        r'who is', 
        r'tell me about', 
        r'give me information on',
        r'can you tell me about',
        r'find details on',
        r'get info on'
    ]
    for pattern in patterns:
        user_message = re.sub(pattern, '', user_message).strip()
    
    return user_message

@app.route('/')
def index():
    return render_template('front.html')

@app.route('/chatbot')
def chat():
    return render_template('chatbot.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    try:
        user_message = request.json.get('message')
        print(f"User message: {user_message}")  # Debugging statement

        # Check if the user is asking for admission process or admission-related info
        if 'admission' in user_message.lower():
            response = get_admission_info()  # Fetch the admission procedure
            return jsonify({'response': response})

        # Check if the user is asking for faculty and contact information
        if 'faculty and contact information' in user_message.lower():
            response = "Sure! Please give me the name or initials of the faculty and I can assist you with further information."
            return jsonify({'response': response})

        # Normalize the user message to handle different forms of input
        normalized_message = normalize_query(user_message)
        print(f"Normalized message: {normalized_message}")  # Debugging statement

        # Initialize response and search for exact matches (first name, last name, or initials)
        matches = []
        if normalized_message:
            for i, row in data.iterrows():
                # Split the name into first and last names
                full_name = row['Faculty_name'].strip().split()
                first_name = full_name[0].lower()  # First name (lowercase for comparison)
                last_name = full_name[-1].lower()  # Last name (lowercase for comparison)
                initials = str(row['Faculty_Initials']).lower()  # Faculty initials (lowercase for comparison)
                
                # Check if the normalized query matches either the first name, last name, or initials
                if normalized_message == first_name or normalized_message == last_name or normalized_message == initials:
                    match = (f"Department: {row['Dpartments']}, Name: {row['Faculty_name']}, "
                             f"Code: {row['Faculty_Initials']}, Email: {row['Email_Id']}, Room No: {row['Room_No']}")
                    matches.append(match)

        # Check if matches are found, otherwise use AI response
        if matches:
            response = '<br>'.join(matches)
        else:
            response = generate_ai_response(user_message)

        print(f"Response: {response}")  # Debugging statement
        return jsonify({'response': response})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'response': "An error occurred on the server"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
