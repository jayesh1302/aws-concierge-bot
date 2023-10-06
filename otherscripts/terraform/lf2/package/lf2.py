import boto3
import json
import requests
from requests_aws4auth import AWS4Auth
from os import getenv
from dotenv import load_dotenv

load_dotenv()
region = 'us-east-1'
service = 'es'
credentials = boto3.Session(
        region_name=region,
        aws_access_key_id=getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=getenv('AWS_SECRET_ACCESS_KEY')
    ).get_credentials()
awsauth = AWS4Auth(credentials.access_key,
                   credentials.secret_key,
                   region, 
                   service,
                   session_token=credentials.token
                   )

host = getenv('ES_HOST')
index = 'restaurant'
url = host + '/' + index + '/_search'

def lambda_handler(event, context):
    sqs = boto3.client('sqs')    
    queue_url = sqs.get_queue_url(QueueName='Q1-test')['QueueUrl']
    print("Polling from: {}".format(queue_url))
    queries = []
    while True:
        response = sqs.receive_message(QueueUrl=queue_url,
                                       MaxNumberOfMessages=10,
                                       WaitTimeSeconds=3
        )
        if 'Messages' not in response:
            break
        for msg in response['Messages']:
            q = json.loads(msg['Body'])
            queries.append(q)
    if not queries:
        response = {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": '*'
                },
                "body": "SNS poll fail or queue is empty. Try again later."
            }
        return response
    restaurant_ids = _query_opensearch_(queries)
    restaurant_infos = _query_dynamno_(restaurant_ids)
    _send_ses_(queries, restaurant_infos)
    # _delete_sqs_msg(sqs, queue_url, messages)

def _send_ses_(queries, restaurant_infos):
    ses = boto3.client("ses")
    CHARSET = "UTF-8"
    for q, info in zip(queries, restaurant_infos):
        print(q)
        email_text = "Hello!\nHere are my {} restaurant suggestions for {} people, for {}:\n1. {}, located at {}"\
        .format(q['cuisine'], q['num_ppl'], q['time'], info['name']['S'], info['address']['S'])
        dest_email = q['email']
        _ = ses.send_email(
            Destination={
                "ToAddresses": [dest_email],
            },
            Message={
                "Body": {
                    "Text":{
                        "Charset": CHARSET,
                        "Data": email_text
                    }
                },
                "Subject": {
                    "Charset": CHARSET,
                    "Data": "Restaurant Recommendation!",
                },
            },
            Source=getenv('SENDER_EMAIL'),
        )
        

def _query_dynamno_(restaurant_ids):
    db = boto3.client('dynamodb')
    restaurant_infos = []
    for _id in restaurant_ids:
        data = db.get_item(
            TableName='yelp-restaurants',
            Key={
                'id': {
                    'S': str(_id)
                }
            }
        )
        restaurant_infos.append(data['Item'])
    return restaurant_infos


# https://docs.aws.amazon.com/opensearch-service/latest/developerguide/search-example.html
def _query_opensearch_(queries):
    restaurant_ids = []
    for q in queries:
        headers = { "Content-Type": "application/json" }
        query = {
            "size": 1,
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "filter": [{
                                "term": {
                                    "cuisine": q['cuisine']
                                }
                            }],
                        }
                    }, 
                    "random_score": {
                    }, 
                    "boost_mode": "replace"
                },
            }
        }
        r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
        if r.status_code != 200:
            response = {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": '*'
                },
                "body": r.text
            }
            return response
        _id = json.loads(r.text)['hits']['hits'][0]['_source']['id']
        restaurant_ids.append(_id)
    return restaurant_ids
    

def _delete_sqs_msg(sqs, queue_url, messages):
    for message in messages:
        dlt_response = sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
        print(dlt_response['ResponseMetadata']['HTTPStatusCode'])

if __name__ == '__main__':
    lambda_handler(1,1)