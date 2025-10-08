from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
from database import store_conversation, get_conversation_history, get_user_session
import logging
import uuid
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(hours=24)
CORS(app)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.before_request
def before_request():
    """Set up session for each user"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session.permanent = True

@app.route('/')
def index():
    """Render the main chat interface"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages and return AI responses"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        if len(user_message) > 1000:
            return jsonify({'error': 'Message too long. Please keep it under 1000 characters.'}), 400
            
        # Get AI response with conversation context
        ai_response = get_ai_response(user_message, session['user_id'])
        
        # Store conversation in MongoDB
        conversation_id = store_conversation(
            user_message, 
            ai_response, 
            session['user_id']
        )
        
        return jsonify({
            'response': ai_response,
            'conversation_id': conversation_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error in chat route: {str(e)}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500

def get_ai_response(message, user_id):
    """Get response from OpenAI API with conversation context"""
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Get recent conversation history for context
        recent_conversations = get_user_session(user_id, limit=5)
        
        # Build conversation context
        messages = [
            {"role": "system", "content": """You are a helpful AI study buddy designed to assist students with their academic questions. 
            You should:
            - Provide clear, educational explanations
            - Break down complex concepts into understandable parts
            - Ask follow-up questions to ensure understanding
            - Encourage learning and critical thinking
            - Be patient and supportive
            - Reference previous conversation if relevant
            - If you don't know something, admit it and suggest resources
            - Keep responses concise but comprehensive"""}
        ]
        
        # Add conversation history for context
        for conv in reversed(recent_conversations):
            messages.append({"role": "user", "content": conv['user_message']})
            messages.append({"role": "assistant", "content": conv['ai_response']})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            presence_penalty=0.6,
            frequency_penalty=0.3
        )
        
        return response.choices.message.content
        
    except openai.RateLimitError:
        return "I'm currently experiencing high demand. Please try again in a moment."
    except openai.AuthenticationError:
        app.logger.error("OpenAI authentication failed")
        return "I'm having authentication issues. Please contact support."
    except Exception as e:
        app.logger.error(f"OpenAI API error: {str(e)}")
        return "I'm having trouble connecting to my knowledge base. Please try again in a moment."

@app.route('/history')
def history():
    """Get conversation history for current user"""
    try:
        conversations = get_user_session(session['user_id'], limit=50)
        return jsonify(conversations)
    except Exception as e:
        app.logger.error(f"Error fetching history: {str(e)}")
        return jsonify({'error': 'Could not fetch conversation history'}), 500

@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear conversation history for current user"""
    try:
        # This would clear the user's session history
        # Implementation depends on your database design
        return jsonify({'message': 'History cleared successfully'})
    except Exception as e:
        app.logger.error(f"Error clearing history: {str(e)}")
        return jsonify({'error': 'Could not clear history'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
