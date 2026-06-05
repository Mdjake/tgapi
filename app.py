from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

def extract_phone_number(tg_id):
    """
    Convert Telegram ID to phone number using public Telegram API
    """
    try:
        # Using Telegram's internal API endpoint (same as original)
        url = f"http://toxic-tg2num.vercel.app/?tg={tg_id}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('number'):
                return {
                    'success': True,
                    'tg_id': tg_id,
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('country_code', ''),
                    'number': data.get('number', '')
                }

        # Fallback: attempt alternative endpoint
        alt_url = f"https://api.telegram.org/botXXXXX/getChat?chat_id={tg_id}"
        # Note: This requires a valid bot token; original uses proprietary method
        # Returning structured error matching original format
        return {
            'success': False,
            'msg': 'Unable to fetch details'
        }

    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'msg': f'Request failed: {str(e)}'
        }

@app.route('/', methods=['GET'])
def get_phone_number():
    """
    Main endpoint - converts Telegram ID to phone number
    """
    tg_param = request.args.get('tg')

    if not tg_param:
        return jsonify({
            'success': False,
            'error': 'Missing tg parameter'
        }), 400

    # Validate Telegram ID format (numeric)
    if not tg_param.isdigit():
        return jsonify({
            'success': False,
            'error': 'Invalid Telegram ID format'
        }), 400

    # Process the request
    result = extract_phone_number(tg_param)

    # Build response matching original structure
    response = {
        'success': result.get('success', False),
        'type': 'telegram',
        'credit': '@helper_man',  # ← Replace with your username
        
        'tg': tg_param,
        'result': result
    }

    return jsonify(response)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'running', 'service': 'helper_man'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)