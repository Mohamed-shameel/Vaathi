from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# MongoDB connection
try:
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['study_buddy']
    conversations_collection = db['conversations']
    
    # Create indexes for better performance
    conversations_collection.create_index([("user_id", 1), ("timestamp", -1)])
    conversations_collection.create_index([("timestamp", 1)], expireAfterSeconds=2592000)  # 30 days
    
    logging.info("Connected to MongoDB successfully")
except Exception as e:
    logging.error(f"MongoDB connection error: {str(e)}")
    client = None

def store_conversation(user_message, ai_response, user_id):
    """Store conversation in MongoDB"""
    try:
        if not client:
            return None
            
        conversation = {
            'user_message': user_message,
            'ai_response': ai_response,
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            'message_length': len(user_message),
            'response_length': len(ai_response)
        }
        
        result = conversations_collection.insert_one(conversation)
        return str(result.inserted_id)
        
    except Exception as e:
        logging.error(f"Error storing conversation: {str(e)}")
        return None

def get_conversation_history(limit=50):
    """Retrieve all conversation history (admin use)"""
    try:
        if not client:
            return []
            
        conversations = conversations_collection.find().sort('timestamp', -1).limit(limit)
        
        history = []
        for conv in conversations:
            history.append({
                'id': str(conv['_id']),
                'user_message': conv['user_message'],
                'ai_response': conv['ai_response'],
                'user_id': conv.get('user_id', 'unknown'),
                'timestamp': conv['timestamp'].isoformat()
            })
            
        return history
        
    except Exception as e:
        logging.error(f"Error fetching conversation history: {str(e)}")
        return []

def get_user_session(user_id, limit=10):
    """Get conversation history for a specific user session"""
    try:
        if not client:
            return []
            
        conversations = conversations_collection.find(
            {'user_id': user_id}
        ).sort('timestamp', -1).limit(limit)
        
        history = []
        for conv in conversations:
            history.append({
                'id': str(conv['_id']),
                'user_message': conv['user_message'],
                'ai_response': conv['ai_response'],
                'timestamp': conv['timestamp'].isoformat()
            })
            
        return history
        
    except Exception as e:
        logging.error(f"Error fetching user session: {str(e)}")
        return []

def get_conversation_stats():
    """Get basic statistics about conversations"""
    try:
        if not client:
            return {}
            
        total_conversations = conversations_collection.count_documents({})
        unique_users = len(conversations_collection.distinct('user_id'))
        
        # Get conversations from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_conversations = conversations_collection.count_documents({
            'timestamp': {'$gte': yesterday}
        })
        
        return {
            'total_conversations': total_conversations,
            'unique_users': unique_users,
            'recent_conversations': recent_conversations
        }
        
    except Exception as e:
        logging.error(f"Error fetching stats: {str(e)}")
        return {}
