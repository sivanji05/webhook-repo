import os
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
from pyngrok import ngrok
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Database Connection ---

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("MONGO_URI environment variable not set!")

client = MongoClient(MONGO_URI)
db = client.techstax_assessment #  database name
events_collection = db.events      #  collection name

# --- Route to Handle Webhooks ---
@app.route('/webhook', methods=['POST'])
def github_webhook():
    """
    Receives webhook events from Github.
    Parses the payload and stores in MongoDB.
    """
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.json
    
    event_data = None

    if event_type == 'push':
        # Push event handling
        pusher = payload['pusher']['name']
        to_branch = payload['ref'].split('/')[-1]
        commit_hash = payload['head_commit']['id']
        timestamp = payload['head_commit']['timestamp']

        event_data = {
            'request_id': commit_hash,
            'author': pusher,
            'action': 'PUSH',
            'from_branch': None, # PUSH doesn't have a 'from' branch
            'to_branch': to_branch,
            'timestamp': timestamp
        }
    
    elif event_type == 'pull_request':
        pr_action = payload['action']
        pr = payload['pull_request']

        if pr_action == 'opened':
            # Pull Request Opened event
            author = pr['user']['login']
            from_branch = pr['head']['ref']
            to_branch = pr['base']['ref']
            pr_id = str(pr['id'])
            timestamp = pr['created_at']

            event_data = {
                'request_id': pr_id,
                'author': author,
                'action': 'PULL_REQUEST',
                'from_branch': from_branch,
                'to_branch': to_branch,
                'timestamp': timestamp
            }
        
        elif pr_action == 'closed' and pr['merged']:
            # --- Brownie Points: Merge Event ---
            # A merge is a 'closed' pull request where 'merged' is true
            author = pr['merged_by']['login']
            from_branch = pr['head']['ref']
            to_branch = pr['base']['ref']
            pr_id = str(pr['id'])
            timestamp = pr['merged_at']

            event_data = {
                'request_id': pr_id,
                'author': author,
                'action': 'MERGE',
                'from_branch': from_branch,
                'to_branch': to_branch,
                'timestamp': timestamp
            }

    if event_data:
        # Insert the data into MongoDB
        events_collection.insert_one(event_data)
        print(f"Stored event: {event_data['action']} by {event_data['author']}")
        return jsonify({'status': 'success', 'message': 'Event processed'}), 200

    return jsonify({'status': 'ignored', 'message': 'Event not handled'}), 200

# --- API Route to Fetch Events for UI ---
@app.route('/events', methods=['GET'])
def get_events():
    """
    Provides the last 20 events to the frontend, sorted by time.
    """
    # Find events, sort by timestamp descending, limit to 20
    events = list(events_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(20))
   
    return jsonify(events)


# --- Route to Serve the Frontend UI ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

if __name__ == '__main__':
  
    # Configure ngrok with authtoken from environment variables
    NGROK_AUTHTOKEN = os.environ.get("PYNGROK_AUTHTOKEN")
    if NGROK_AUTHTOKEN:
        ngrok.set_auth_token(NGROK_AUTHTOKEN)
        
        # Start ngrok tunnel
        public_url = ngrok.connect(5000)
        print("===================================================================")
        print(f" * Ngrok tunnel is active at: {public_url}")
        print(" * Use this URL for your GitHub webhook.")
        print("===================================================================")
    else:
        print("Warning: PYNGROK_AUTHTOKEN not found. Running without ngrok.")
        print("Access the app at: http://localhost:5000")

    app.run(debug=True, port=5000, host='0.0.0.0', threaded=True, use_reloader=False)