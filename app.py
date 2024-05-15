from flask import Flask, jsonify, request, render_template, Response
import json
import requests
from flask_basicauth import BasicAuth
import logging
from config import TRANSLATION_API_KEY, WEATHER_API_KEY

from google.cloud import dialogflowcx_v3beta1 as dialogflow
from google.api_core.exceptions import InvalidArgument
from google.cloud.dialogflowcx_v3beta1.types import WebhookRequest, QueryResult
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import MessageToJson


app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'username'
app.config['BASIC_AUTH_PASSWORD'] = 'password'
basic_auth = BasicAuth(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# define a route for translation

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    if 'fulfillmentInfo' not in req or 'tag' not in req['fulfillmentInfo']:
        return jsonify({"error": "Invalid request, tag missing"}), 400

    tag = req['fulfillmentInfo']['tag']
    parameters = req.get('sessionInfo', {}).get('parameters', {})  # Correct parameters extraction

    if tag == "TranslateText_fulfillment":
        return handle_translate_request(parameters)
    else:
        return jsonify({"error": "Unknown tag"}), 400

def handle_translate_request(parameters):
    text = parameters.get('textToTranslate')
    language_code = parameters.get('language')
    if not text or not language_code:
        return jsonify({"error": "Missing text or language code"}), 400

    # Check if the language code is valid
    valid_languages = ['en', 'tw', 'gaa', 'ee', 'fat', 'dag', 'gur', 'yo', 'ki', 'luo', 'mer']
    if language_code not in valid_languages:
        return jsonify({"error": "Invalid language code"}), 400

    return translate_text(text, language_code)

def translate_text(text, language_code):
    api_url = "https://translation-api.ghananlp.org/v1/translate"
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': TRANSLATION_API_KEY
    }
    payload = {
        "in": text,
        "lang": f"{language_code}-en"  # Assuming translation to English
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        logging.debug(f"API response JSON: {response_json}")

        if isinstance(response_json, str):
            translated_text = response_json
        elif 'translatedText' in response_json:
            translated_text = response_json['translatedText']
        else:
            logging.error("Translation API did not return 'translatedText' or a direct string.")
            return jsonify({"error": "Translation failed"}), 500

        return jsonify({
            "fulfillment_response": {
                "messages": [{
                    "text": {
                        "text": [translated_text]
                    }
                }]
            }
        })
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during translation API request: {e}")
        return jsonify({"error": str(e)}), 500

def test_webhook():
    try:
        # Adjust the test payload to match how Dialogflow CX sends parameters
        test_payload = {
            "fulfillmentInfo": {
                "tag": "TranslateText_fulfillment"
            },
            "sessionInfo": {  # Ensure parameters are nested within sessionInfo
                "parameters": {
                    "textToTranslate": "Hello, how are you?",
                    "language": "tw"
                }
            }
        }

        # Using test_request_context to simulate a POST request
        with app.test_request_context('/webhook', method='POST', json=test_payload):
            response = webhook()
            if isinstance(response, tuple):
                response, status = response  # Handling the tuple response
            else:
                status = 200  # Default status if response isn't a tuple

            # Extracting JSON data from the response
            response_data = response.get_json()
            print(response_data, status)

    except Exception as e:
        print(f"Error during webhook testing: {e}")



### Define a Route for weather
@app.route('/my_webhook', methods=['POST'])
def post_webhook_dialogflow():
    body = request.get_json(silent=True)
    if not body or 'fulfillmentInfo' not in body or 'tag' not in body['fulfillmentInfo']:
        return jsonify({"error": "Invalid JSON data"}), 400

    fulfillment = body['fulfillmentInfo']['tag']
    parameters = []
    if 'parameters' in body.get('sessionInfo', {}):
        for key, value in body['sessionInfo']['parameters'].items():
            parameters.append({'name': key, 'value': value})
    else:
        return jsonify({"error": "No parameters provided"}), 400

    msg = invoke_action(fulfillment, parameters)
    return answer_webhook(msg)

def invoke_action(fulfillment, parameters):
    if fulfillment == "GetWeather_fulfillment":
        city = next((p['value'] for p in parameters if p['name'] == "city"), None)
        if not city:
            return "City parameter is missing."

        appid = WEATHER_API_KEY
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={appid}'
        try:
            result = requests.get(url)
            if result.status_code == 200:
                weatherCondition = result.json().get('weather', [{}])[0].get('description', "No description available")
                return f"There is {weatherCondition} in {city}."
            else:
                return f"Failed to retrieve the weather data: {result.text}"
        except Exception as e:
            return f"An error occurred: {str(e)}"

from flask import make_response

def answer_webhook(msg):
    message = {
        "fulfillment_response": {
            "messages": [{
                "text": {
                    "text": [msg]
                }
            }]
        }
    }
    response = make_response(json.dumps(message))
    response.mimetype = 'application/json'
    return response

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
    test_webhook()
