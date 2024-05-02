from flask import Flask, jsonify, request, render_template

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

# @app.route('/translate', methods=['POST'])
# def translate_text():
#     data = request.json
#     # Extract text and target language from Dialogflow CX request
#     # Adjust the JSON path as needed based on your specific Dialogflow CX setup
#     text_to_translate = data['fulfillmentInfo']['text']
#     target_language = 'en-tw'  # Example: English to Twi
#
#     # GhanaNLP API request setup
#     headers = {
#         'Content-Type': 'application/json',
#         'Cache-Control': 'no-cache',
#         'Ocp-Apim-Subscription-Key': '5ff73af047eb4ba6bd3b699b19f81cd0'
#     }
#     payload = {
#         'in': text_to_translate,
#         'lang': target_language
#     }
#
#     # Make the POST request to GhanaNLP API
#     response = requests.post('https://translation-api.ghananlp.org/v1/translate', json=payload, headers=headers)
#     translated_text = response.json()['translatedText']
#
#     # Prepare the response for Dialogflow CX
#     return jsonify({
#         'fulfillment_response': {
#             'messages': [{
#                 'text': {
#                     'text': [translated_text]
#                 }
#             }]
#         }
#     })
### Define a Route
@app.route('/my_webhook', methods=['POST'])
### Define the function that will be executed when the associated route is called

def post_webhook_dialogflow():
    # 1) Getting information from dialogflow agent request
    body = request.get_json(silent=True)

    # Get tag used to identify which fulfillment is being called.
    fulfillment = body['fulfillmentInfo']['tag']

    # Get parameters that are required to handle the desired action
    prameters = []
    for key, value in body['sessionInfo']['parameters'].items():
        prameters.append({'name': key, 'value': value})

    # 2) Execute action
    msg = invoke_action(fulfillment, prameters)

    # 3) provide a webhook Response to the Dialogflow Agent
    WebhookResponse = answer_webhook(msg)
    return WebhookResponse


### Exploit parameters and incorporate them in the text response
def invoke_action(fulfillment, prameters):
    print("\n\n\n\n\n=========> CALL API ",fulfillment)
    if fulfillment == "GetWeather_fulfillment":
        for prameter in prameters:
             if prameter['name']=="city":
                 city=str(prameter['value'])
        appid="25e5d7b2fff948d0749a8b9e9e14f5f9"
        url = 'http://api.openweathermap.org/data/2.5/weather?q='+city+'&appid='+appid
        result = requests.get(url)
        jsonResult = result.json()
        if result.status_code == 200:
            weatherCondition = jsonResult['weather'][0]['description']
            reply = "There is {} there.".format(weatherCondition)
            print(reply)
            return reply
        else:
            return "Something wrong with the API."


#### Processes the webhook answer which should follow a particular JSON format
def answer_webhook(msg):
    message = {"fulfillment_response": {

        "messages": [
            {
                "text": {
                    "text": [msg]
                }
            }
        ]
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
