import boto3
import json
from os import getenv
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def read_data(fn):
    with open(fn , 'r') as f:
        lis = json.load(f)
    return lis

def batch_write2db(data, db):
    table = db.Table('yelp-restaurants')
    batch_size = len(data)//MAX_BATCH_SIZE
    remaining_batches = batch_size
    start_index = -batch_size

    while remaining_batches > 0:
        start_index = start_index+batch_size
        with table.batch_writer() as batch:
            for restaurant in data[start_index:start_index+batch_size]:
                batch.put_item(Item=restaurant)
        remaining_batches -= 1

def batch_write2opensearch(data, es):
    batch_size = len(data)//MAX_BATCH_SIZE
    start_index = -batch_size
    remaining_batches = batch_size

    while remaining_batches > 0:
        for restaurant in data[start_index:start_index + batch_size]:
            es.index(index='restaurant', doc_type='doc', body={
                "id": restaurant["id"],
                "cuisine": restaurant["cuisine_type"],
            })
        remaining_batches -= 1

if __name__ == '__main__': 
    credentials = boto3.Session(
        region_name='us-east-1', \
        aws_access_key_id=getenv('AWS_ACCESS_KEY_ID'), \
        aws_secret_access_key=getenv('AWS_SECRET_ACCESS_KEY')
    ).get_credentials()
    awsauth = AWS4Auth(credentials.access_key,
                       credentials.secret_key, 'us-east-1', 'es')
    es = Elasticsearch(
        hosts=[{'host': getenv('ES_HOST'), 'port': 443}],
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        http_auth=awsauth
    )

    db = boto3.resource('dynamodb')
    MAX_BATCH_SIZE=25
    data = read_data('restaurants.json')
    batch_write2db(data, db)
    batch_write2opensearch(data, es)
