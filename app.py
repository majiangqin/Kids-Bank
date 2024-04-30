from flask import Flask, jsonify, request, render_template

from flask_basicauth import BasicAuth

app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'username'
app.config['BASIC_AUTH_PASSWORD'] = 'password'
basic_auth = BasicAuth(app)


@app.route('/webhook', methods=['POST'])
@basic_auth.required
def webhook():
    # Your webhook logic here
    return jsonify(message='This is a secure area')


@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.json
    # Extract text and target language from Dialogflow CX request
    # Adjust the JSON path as needed based on your specific Dialogflow CX setup
    text_to_translate = data['fulfillmentInfo']['text']
    target_language = 'en-tw'  # Example: English to Twi

    # GhanaNLP API request setup
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Ocp-Apim-Subscription-Key': '5ff73af047eb4ba6bd3b699b19f81cd0'
    }
    payload = {
        'in': text_to_translate,
        'lang': target_language
    }

    # Make the POST request to GhanaNLP API
    response = requests.post('https://translation-api.ghananlp.org/v1/translate', json=payload, headers=headers)
    translated_text = response.json()['translatedText']

    # Prepare the response for Dialogflow CX
    return jsonify({
        'fulfillment_response': {
            'messages': [{
                'text': {
                    'text': [translated_text]
                }
            }]
        }
    })


# Route to serve the HTML page
@app.route('/')
def index():
    return render_template('index.html')

# Assuming balance is stored on the server for the sake of simplicity
balance = 0

@app.route('/balance', methods=['GET'])
def get_balance():
    return jsonify({'balance': balance})

@app.route('/deposit', methods=['POST'])
def deposit():
    global balance
    amount = request.json['amount']
    balance += amount
    return jsonify({'balance': balance})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    global balance
    amount = request.json['amount']
    if balance >= amount:
        balance -= amount
        return jsonify({'balance': balance})
    else:
        return jsonify({'error': 'Insufficient funds'}), 400

if __name__ == '__main__':
    app.run(debug=True)
