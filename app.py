from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ORIGINAL_API_URL = "http://Api.subhxcosmo.in/api"
ORIGINAL_API_KEY = os.environ.get("API_KEY", "KRISHRDP2")

@app.route('/api')
def proxy():
    # Extract parameters from the incoming request
    req_type = request.args.get('type')
    term = request.args.get('term')
    
    # Prepare parameters for the original API
    params = {
        'key': ORIGINAL_API_KEY,
        'type': req_type,
        'term': term
    }
    
    # Fetch data from the original API
    try:
        response = requests.get(ORIGINAL_API_URL, params=params)
        data = response.json()
    except Exception as e:
        return jsonify({"error": "Failed to fetch data", "details": str(e)}), 500
    
    # Clone and modify the response data
    if data.get('success') and 'result' in data:
        # Keep only country_code and number, then change the credit
        modified_result = {
            'country_code': data['result'].get('country_code'),
            'number': data['result'].get('number')
        }
        cloned_data = {
            "developer": "helper man",
            "data": modified_result
        }
        return jsonify(cloned_data)
    else:
        return jsonify({"error": "Invalid response from original API"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)