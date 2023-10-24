import json
import boto3
import re
from datetime import datetime

# Initialize SQS client
sqs = boto3.client('sqs')
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/764559909612/Q1'

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

def close(session_attributes, fulfillment_state, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def validate_slots(location, dining_date, dining_time, num_ppl, cuisine, email):
    # Check if date and time is in the future
    current_datetime = datetime.now()
    dining_datetime = datetime.strptime(f"{dining_date} {dining_time}", "%Y-%m-%d %H:%M")
    if dining_datetime <= current_datetime:
        return "Please ensure the dining date and time are in the future."
    
    # Check location
    supported_locations = ["nyc", "new york", "manhattan", "big apple", "ny"]
    if location.lower() not in supported_locations:
        return "We only support the New York Area. Please try again later."
    
    # Check number of people
    if int(num_ppl) < 1:
        return "Please enter a minimum of 1 guest."
    
    # Check cuisine
    supported_cuisines = ["chinese", "indpak", "italian"]
    if cuisine.lower() not in supported_cuisines:
        return "We only support the following cuisines: chinese, indpak, italian."
    
    # Check email format. Although email validations are taken care by Lex, adding some more checks in case missed
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    if not re.match(email_regex, email):
        return "Please provide a valid email address."

    return None

def lambda_handler(event, context):
    intent_name = event['currentIntent']['name']

    # GreetingIntent
    if intent_name == "GreetingIntent":
        return close({}, 'Fulfilled', {
            'contentType': 'PlainText',
            'content': 'Hi there, how can I help?'
        })

    # ThankYouIntent
    elif intent_name == "ThankYouIntent":
        return close({}, 'Fulfilled', {
            'contentType': 'PlainText',
            'content': "You're welcome! Let me know if there's anything else."
        })

    # DiningSuggestionsIntent
    elif intent_name == "DiningSuggestionsIntent":
        # Extract slot values
        slots = event['currentIntent']['slots']
        location = slots['location']
        cuisine = slots['cuisine']
        dining_date = slots['date']
        dining_time = slots['time']
        number_of_people = slots['num_ppl']
        email = slots['email']

        # Validate the slots
        validation_error = validate_slots(location, dining_date, dining_time, number_of_people, cuisine, email)
        if validation_error:
            return close({}, 'Failed', {
                'contentType': 'PlainText',
                'content': validation_error
            })

        # Push to SQS
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps({
                'location': location,
                'cuisine': cuisine,
                'date': dining_date,
                'time': dining_time,
                'num_ppl': number_of_people,
                'email': email
            })
        )

        return close({}, 'Fulfilled', {
            'contentType': 'PlainText',
            'content': 'Thank you! I have received your request. You will be notified over email once we have the list of restaurant suggestions.'
        })

    # Handle other intents (if any)
    else:
        return close({}, 'Failed', {
            'contentType': 'PlainText',
            'content': "Sorry, I couldn't process your request."
        })
