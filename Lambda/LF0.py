import json,datetime,boto3,logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    logger.debug(f"Function triggered")
    message = event['messages']
    logger.debug(message)
    bot_response_message = "Please Try again!"
    
    if message is not None or len(message) > 0:
        data = message[0]['unstructured']['text']
        client = boto3.client('lex-runtime')
        bot_response = client.post_text(botName='ChatBotDining', botAlias='Ourbot', userId='dev', inputText= data)
        bot_response_message = bot_response['message']
    
    response = {
        'messages': [
            {
                "type":"unstructured",
                "unstructured": {
                    "id":"1",
                    "text": bot_response_message,
                    "timestamp": str(datetime.datetime.now().timestamp())
                }
            }
            ]
    }
    logger.debug(f"Sending response {response}")
    return response