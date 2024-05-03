from flask import Flask, jsonify, request, render_template, Response
import json
import requests
from flask_basicauth import BasicAuth

app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'username'
app.config['BASIC_AUTH_PASSWORD'] = 'password'
basic_auth = BasicAuth(app)


@app.route('/webhook', methods=['POST'])
@basic_auth.required
def webhook():
    req = request.get_json(force=True)
    text_to_translate = req['queryResult']['parameters']['textToTranslate']
    target_language = req['queryResult']['parameters']['language']

    translated_text = translate_text(text_to_translate, target_language)
    return jsonify(fulfillment_response={"messages": [{"text": {"text": [translated_text]}}]})

def translate_text(text, language_code):
    # Assume you have the API URL and your API key for the GhanaNLP API
    api_url = "https://translation-api.ghananlp.org/v1/translate"
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': '5ff73af047eb4ba6bd3b699b19f81cd0'
    }
    payload = {
        'in': text,
        'lang': language_code
    }
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()['translatedText']

### Define a Route for weather
@app.route('/my_webhook', methods=['POST'])
def post_webhook_dialogflow():
    body = request.get_json(silent=True)
    fulfillment = body['fulfillmentInfo']['tag']
    parameters = []
    for key, value in body['sessionInfo']['parameters'].items():
        parameters.append({'name': key, 'value': value})
    msg = invoke_action(fulfillment, parameters)
    return answer_webhook(msg)

def invoke_action(fulfillment, parameters):
    print("\n\n\n\n\n=========> CALL API ", fulfillment)
    if fulfillment == "GetWeather_fulfillment":
        city = next((p['value'] for p in parameters if p['name'] == "city"), None)
        appid = "a363a549449568db4fe82c04a2a33c73"
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={appid}'
        try:
            result = requests.get(url)
            jsonResult = result.json()
            if result.status_code == 200:
                weatherCondition = jsonResult['weather'][0]['description']
                reply = f"There is {weatherCondition} in {city}."
                return reply
            else:
                return "Failed to retrieve the weather data."
        except Exception as e:
            return f"An error occurred: {str(e)}"

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
    return Response(json.dumps(message), 200, mimetype='application/json')


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
