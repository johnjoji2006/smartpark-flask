from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- In-Memory Database ---
# Status: 'empty' or 'occupied'
cards = {
    1: {'id': 1, 'status': 'empty', 'vehicle': None, 'entryTime': None, 'phone': None},
    2: {'id': 2, 'status': 'empty', 'vehicle': None, 'entryTime': None, 'phone': None},
    3: {'id': 3, 'status': 'empty', 'vehicle': None, 'entryTime': None, 'phone': None},
}

@app.route('/')
def home():
    return render_template('index.html')

# --- API Endpoints ---

@app.route('/api/status', methods=['GET'])
def get_status():
    """Returns the current status of all cards."""
    return jsonify(cards)

@app.route('/api/update', methods=['POST'])
def update_card():
    """Updates a card's status (Check-In or Check-Out)."""
    data = request.json
    card_id = int(data.get('cardId'))
    action = data.get('action') # 'checkin' or 'checkout'
    
    if card_id not in cards:
        return jsonify({'error': 'Invalid Card ID'}), 400
    
    if action == 'checkin':
        cards[card_id]['status'] = 'occupied'
        cards[card_id]['vehicle'] = data.get('vehicle').upper()
        cards[card_id]['phone'] = data.get('phone')
        cards[card_id]['entryTime'] = datetime.now().isoformat()
        return jsonify({'message': 'Check-In Successful', 'card': cards[card_id]})
    
    elif action == 'checkout':
        # Reset card
        cards[card_id]['status'] = 'empty'
        cards[card_id]['vehicle'] = None
        cards[card_id]['phone'] = None
        cards[card_id]['entryTime'] = None
        return jsonify({'message': 'Check-Out Successful', 'card': cards[card_id]})

    return jsonify({'error': 'Invalid Action'}), 400

if __name__ == '__main__':
    # Run slightly different for local vs production (Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
