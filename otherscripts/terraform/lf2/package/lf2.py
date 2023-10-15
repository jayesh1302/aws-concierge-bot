import boto3
import json
import requests
from requests_aws4auth import AWS4Auth
from os import getenv
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

region = 'us-east-1'
service = 'es'
credentials = boto3.Session(region_name=region).get_credentials()
awsauth = AWS4Auth(credentials.access_key,
                   credentials.secret_key,
                   region,
                   service,
                   session_token=credentials.token
                   )
index = 'restaurant'
queue_url = getenv('TF_VAR_sqs_url')
url = getenv('TF_VAR_es_host') + '/' + index + '/_search'

def _return_response(msg, statusCode):
    response = {
                "statusCode": statusCode,
                "headers": {
                    "Access-Control-Allow-Origin": '*'
                },
                "body": msg
            }
    return response

def lambda_handler(event, context):
    sqs = boto3.client('sqs')
    logger.info("Polling from: {}".format(queue_url))
    queries = []
    messages = []
    while True:
        response = sqs.receive_message(QueueUrl=queue_url,
                                       MaxNumberOfMessages=10,
                                       WaitTimeSeconds=7
                                       )
        if 'Messages' not in response:
            break
        messages += response['Messages']
    if not messages:
        msg = _return_response("SQS poll fail or queue is empty. Try again later.", 200)
        logger.error(msg)
        return msg
    queries = []
    for msg in messages:
        queries.append(json.loads(msg['Body']))
    try:
        restaurant_ids = _query_opensearch_(queries)
        restaurant_infos = _query_dynamno_(restaurant_ids)
        _send_ses_(queries, restaurant_infos)
        _delete_sqs_msg(sqs, queue_url, messages)
    except Exception as e:
        msg = _return_response(str(e), 500)
        logger.error(msg)
        return msg
    msg = _return_response("Recommendations have been sent out!", 200)
    logger.info(msg)
    return msg

def _send_ses_(queries, restaurant_infos):
    ses = boto3.client("ses")
    CHARSET = "UTF-8"
    for q, info in zip(queries, restaurant_infos):
        email_text = "Hello!\nHere are my {} restaurant suggestions for {} people, for {} at {}:\n1. {}, located at {}"\
        .format(q['cuisine'], q['num_ppl'], q['date'], q['time'], info['name']['S'], info['address']['S'])
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
            Source=getenv('TF_VAR_sender_email'),
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
                                    "cuisine": q['cuisine'].lower()
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
        r = requests.get(url,
                         auth=awsauth,
                         headers=headers,
                         data=json.dumps(query),
                         timeout=10
                         )
        if r.status_code != 200:
            raise Exception("OpenSearch query failed: {}".format(r.text))
        _id = json.loads(r.text)['hits']['hits'][0]['_source']['id']
        restaurant_ids.append(_id)
    return restaurant_ids
    

def _delete_sqs_msg(sqs, queue_url, messages):
    for message in messages:
        dlt_response = sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
        logger.info("SQS delete message response: {}".format(dlt_response['ResponseMetadata']['HTTPStatusCode']))

if __name__ == '__main__':
    lambda_handler(1,1)