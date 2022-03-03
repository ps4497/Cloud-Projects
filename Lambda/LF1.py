import imp
import math
from unittest import result
from wsgiref import validate
from datetime import datetime, timedelta
import time
import os
import logging
import json
import boto3
# import phonenumbers as ph
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
SQS_QUEUE = os.environ['SQS']

# Check if all the parameters are valid, if not return ElicitSlot
# Return CloseIntent after sending the message to sqs


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def publishToSQS(slots):
    logger.debug("Intent is Dining Suggestions, Entered publishToSQS")
    sqs = boto3.client('sqs')

    try:
        response = sqs.send_message(
            QueueUrl=SQS_QUEUE,
            DelaySeconds=0,
            MessageAttributes={
                'cuisine': {
                    'DataType': 'String',
                    'StringValue': slots['cuisine']
                },
                'location': {
                    'DataType': 'String',
                    'StringValue': slots['location']
                },
                'email': {
                    'DataType': 'String',
                    'StringValue': slots['email']
                },
                'time': {
                    'DataType': 'String',
                    'StringValue': slots['time']
                },
                'date': {
                    'DataType': 'String',
                    'StringValue': slots['date']
                },
                'number': {
                    'DataType': 'Number',
                    'StringValue': slots['number']
                }
            },
            MessageBody=(
                'Details for Dining'
            )
        )
        logger.info(response)
    except ClientError as e:
        logging.error(e)
        return None
    return response


def buildmsg(msg):
    return {'contentType': 'PlainText', 'content': msg}


def dispatchelicitSlot(event, slotToElicit, message):
    logger.info(f"Entered Invalid Slot value for {slotToElicit}")
    return {
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': event['currentIntent']['name'],
            'slots': event['currentIntent']['slots'],
            'slotToElicit': slotToElicit,
            'message': message
        }
    }


def handleDiningSuggestionsIntent(event):
    logger.info("handing Dining Intent")

    slots = event['currentIntent']['slots']

    logger.debug(slots)

    # validate parameters

    if not slots['location']:
        return dispatchelicitSlot(event, 'location', buildmsg("where do you want to eat?"))

    if slots['location'].lower() not in ['manhattan', 'newyork', 'ny', 'nyc']:
        return dispatchelicitSlot(event, 'location', buildmsg("We did not find anything there, enter a different location"))

    if not slots['cuisine']:
        return dispatchelicitSlot(event, 'cuisine', buildmsg("what cuisine do you want to eat?"))

    if slots['cuisine'].lower() not in ['chinese', 'indian', 'middleeastern', 'italian', 'mexican']:
        return dispatchelicitSlot(event, 'cuisine', buildmsg("Hmm.. didnt find anything for that cusisine, enter a different one"))

    if not slots['number']:
        return dispatchelicitSlot(event, 'number', buildmsg("Please Enter Number of People for Dining"))

    if int(slots['number']) < 0:
        return dispatchelicitSlot(event, 'number', buildmsg("Please Enter Positive Number only"))

    if int(slots['number']) > 100:
        return dispatchelicitSlot(event, 'number', buildmsg("Sorry max capacity is 100, please Enter number less than 100"))

    if not slots['date']:
        return dispatchelicitSlot(event, 'date', buildmsg("Please Enter Dining Date"))

    if slots['date']:
        logger.debug("entered date validation")
        current_time = datetime.now()
        entered = datetime.strptime(
            slots['date']+" "+datetime.now().strftime("%H:%M:%S"), '%Y-%m-%d %H:%M:%S') + timedelta(seconds=5)
        logger.debug(f"Entered Date: {entered}")
        logger.debug(f"Entered Date: {current_time}")
        if(entered < current_time):
            return dispatchelicitSlot(event, 'date', buildmsg("Sorry, cannot make reservation in the past, enter date agin"))

    if not slots['time']:
        return dispatchelicitSlot(event, 'time', buildmsg("Please Enter Dining Time"))

    if slots['time']:
        logger.debug("entered time validation")
        entered = datetime.strptime(
            slots['date']+" "+slots['time'], '%Y-%m-%d %H:%M')
        logger.debug("Entered Time: {entered}")
        if(datetime.now() > entered):
            return dispatchelicitSlot(event, 'date', buildmsg("Sorry, cannot make reservation in the past, enter time agin"))

    if not slots['email']:
        return dispatchelicitSlot(event, 'email', buildmsg("Please Enter your email address"))
        
    if slots['email']:
        email_address = slots['email']
        if slots['email'].split("@")[1] not in ["gmail.com", "nyu.edu"]:
            return dispatchelicitSlot(event, 'email', buildmsg("The email address provided is not valid. Please Enter a valid email address"))

    result = publishToSQS(slots)
    lambdaclient = boto3.client('lambda')
    response = lambdaclient.invoke(
        FunctionName='LF2',
        InvocationType='Event'
    )
    # text = json.load(response['Payload'])
    print(result)

    return {
        "dialogAction":
        {
            "fulfillmentState": "Fulfilled" if result else "Failed",
            "type": "Close",  # Informs Amazon Lex not to expect a response from the user
            "message": {
                    "contentType": "PlainText",  # "PlainText or SSML or CustomPayload"
                    "content": 'I have collected a few trendy options for you, I will sent detailed information to your email address:{}'.format(email_address) if result else "Try Again"
            }
        }
    }


def handleGreetingIntent(event):
    logger.info("handing Greeting Intent")
    return {
        "dialogAction":
            {
                "fulfillmentState": "Fulfilled",  # or Failed
                "type": "Close",  # Informs Amazon Lex not to expect a response from the user
                "message":
                {
                    "contentType": "PlainText",  # "PlainText or SSML or CustomPayload"
                    "content": "Hi there, How can I help?",
                }
            }
    }
    

def handleThankingIntent(event):
    logger.info("handing Greeting Intent")
    return {
        "dialogAction":
            {
                "fulfillmentState": "Fulfilled",  # or Failed
                "type": "Close",  # Informs Amazon Lex not to expect a response from the user
                "message":
                {
                    "contentType": "PlainText",  # "PlainText or SSML or CustomPayload"
                    "content": "Welcome!! Have a Nice Day!!",
                }
            }
    }


def errordispatch(event):
    logger.debug('dispatch userId={}, intentName={}'.format(
        event['userId'], event['currentIntent']['name']))

    return {
        "dialogAction":
            {
                "fulfillmentState": "Failed",  # or Failed
                "type": "Close",  # Informs Amazon Lex not to expect a response from the user
                "message":
                {
                    "contentType": "PlainText",  # "PlainText or SSML or CustomPayload"
                    "content": "Something's Wrong",
                }
            }
    }


def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.info('event.bot.name={}'.format(event['bot']['name']))
    logger.info(f"userId: {event['userId']}")
    logger.info(f"Intent: {event['currentIntent']['name']}")
    logger.info(f"invocationSource: {event['invocationSource']}")
    logger.info(f" Messages Bus:  {SQS_QUEUE}")

    if event['currentIntent']['name'] == "DiningIntent":
        return handleDiningSuggestionsIntent(event)
    if event['currentIntent']['name'] == "GreetingIntent":
        return handleGreetingIntent(event)
    if event['currentIntent']['name'] == "Thanking":
        return handleThankingIntent(event)
    else:
        return errordispatch(event)
