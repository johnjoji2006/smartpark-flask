from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# In-memory database
# Keyed by ID as strings to match frontend expectation
cards_data = {
    "1": {"id": 1, "status": "empty", "vehicle": "None", "entryTime": None},
    "2": {"id": 2, "status": "occupied", "vehicle": "KA-53-Z-9021", "entryTime": datetime.now().isoformat()},
    "3": {"id": 3, "status": "empty", "vehicle": "None", "entryTime": None}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(cards_data)

@app.route('/api/update', methods=['POST'])
def update_status():
    data = request.json
    card_id = str(data.get('cardId'))
    action = data.get('action')
    
    if card_id in cards_data:
        if action == 'checkin':
            cards_data[card_id]['status'] = 'occupied'
            cards_data[card_id]['vehicle'] = data.get('vehicle', 'Unknown')
            cards_data[card_id]['phone'] = data.get('phone', '')
            cards_data[card_id]['entryTime'] = datetime.now().isoformat()
        
        elif action == 'checkout':
            cards_data[card_id]['status'] = 'empty'
            cards_data[card_id]['vehicle'] = 'None'
            cards_data[card_id]['entryTime'] = None
            
    return jsonify({"message": "Success", "data": cards_data[card_id]})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
