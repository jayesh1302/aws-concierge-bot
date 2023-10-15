import json
import boto3

def lambda_handler(event, context):
    
    lexClient = boto3.client('lex-runtime')
    print(event)
    body_content = json.loads(event['body'])
    inputText = body_content['messages'][0]['unstructured']['text']
    lexResponse = lexClient.post_text(
        botName='DiningBot',
        botAlias='diningBotAlias',
        userId='user123',
        inputText=inputText
    )
    
    print(lexResponse)
      
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*", 
            "Access-Control-Allow-Credentials": True,
            "Access-Control-Allow-Headers": "Content-Type", 
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        "body": json.dumps({
            "messages": [
                {
                    "type": "unstructured",
                    "unstructured": {
                        "id": 1,
                        "text": lexResponse['message'],
                        "timestamp": "10-13-2023"
                    }
                }
            ]
        })
    }
    return response
