"""HTTP routes for the study buddy application."""

import logging
import os
import uuid
from datetime import datetime

import openai
from flask import jsonify, render_template, request, session

from .database import get_user_session, store_conversation


def register_routes(app):
    @app.before_request
    def set_up_session():
        if "user_id" not in session:
            session["user_id"] = str(uuid.uuid4())
            session.permanent = True

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/chat", methods=["POST"])
    def chat():
        try:
            data = request.get_json()
            user_message = data.get("message", "").strip()

            if not user_message:
                return jsonify({"error": "No message provided"}), 400
            if len(user_message) > 1000:
                return jsonify({"error": "Message too long. Please keep it under 1000 characters."}), 400

            ai_response = get_ai_response(user_message, session["user_id"], app)
            conversation_id = store_conversation(user_message, ai_response, session["user_id"])
            return jsonify({
                "response": ai_response,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception as error:
            app.logger.error("Error in chat route: %s", error)
            return jsonify({"error": "Something went wrong. Please try again."}), 500

    @app.route("/history")
    def history():
        try:
            return jsonify(get_user_session(session["user_id"], limit=50))
        except Exception as error:
            app.logger.error("Error fetching history: %s", error)
            return jsonify({"error": "Could not fetch conversation history"}), 500

    @app.route("/clear", methods=["POST"])
    def clear_history():
        return jsonify({"message": "History cleared successfully"})

    @app.errorhandler(404)
    def not_found(error):
        return render_template("index.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500


def get_ai_response(message, user_id, app):
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        recent_conversations = get_user_session(user_id, limit=5)
        messages = [{
            "role": "system",
            "content": """You are a helpful AI study buddy designed to assist students with academic questions. Provide clear educational explanations, break down complex concepts, encourage learning, and keep responses concise but comprehensive.""",
        }]

        for conversation in reversed(recent_conversations):
            messages.append({"role": "user", "content": conversation["user_message"]})
            messages.append({"role": "assistant", "content": conversation["ai_response"]})
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            presence_penalty=0.6,
            frequency_penalty=0.3,
        )
        return response.choices[0].message.content
    except openai.RateLimitError:
        return "I'm currently experiencing high demand. Please try again in a moment."
    except openai.AuthenticationError:
        app.logger.error("OpenAI authentication failed")
        return "I'm having authentication issues. Please contact support."
    except Exception as error:
        app.logger.error("OpenAI API error: %s", error)
        return "I'm having trouble connecting to my knowledge base. Please try again in a moment."
