import boto3
import json
from decimal import Decimal
from os import getenv
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from dotenv import load_dotenv
from datetime import datetime

def read_data(fn):
    with open(fn , 'r') as f:
        restaurants = json.load(f, parse_float=Decimal)
    return restaurants
def drop_table(dyn_resource):
    """
    Deletes the demonstration table.

    :param dyn_resource: Either a Boto3 or DAX resource.
    """
    try:
        dyn_resource = boto3.resource('dynamodb')
    except:
        return
    table = dyn_resource.Table('yelp-restaurants')
    table.delete()

    print(f"Deleting {table.name}...")
    table.wait_until_not_exists()
                      
def batch_write2db(data, db):
    table = db.Table('yelp-restaurants')
    batch_size = len(data)//MAX_BATCH_SIZE
    start_index = 0
    while batch_size > 0:
        with table.batch_writer() as batch:
            for restaurant in data[start_index:start_index+MAX_BATCH_SIZE]:
                restaurant["insertedAtTimestamp"] = datetime.now().isoformat()
                batch.put_item(Item=restaurant)
        start_index += MAX_BATCH_SIZE
        batch_size -= 1
    if start_index < len(data):
        with table.batch_writer() as batch:
            for restaurant in data[start_index:]:
                batch.put_item(Item=restaurant)

def batch_write2opensearch(data, es):
    batch_size = len(data)//MAX_BATCH_SIZE
    start_index = 0

    while batch_size > 0:
        for restaurant in data[start_index:start_index+MAX_BATCH_SIZE]:
            es.index(index='restaurant', doc_type='_doc', body={
                "id": restaurant["id"],
                "cuisine": restaurant["cuisine_type"],
            })
        start_index += MAX_BATCH_SIZE
        batch_size -= 1
    if start_index < len(data):
        for restaurant in data[start_index:]:
            es.index(index='restaurant', doc_type='doc', body={
                "id": restaurant["id"],
                "cuisine": restaurant["cuisine_type"],
            })
def check_opensearch_data(es):
    res = es.search(
        index="restaurant",
        body={
            "query": {
                "match": {
                    "cuisine": 'chinese'
                }
                }
            }
        )
    print("Got %d Hits" % res['hits']['total']['value'])

if __name__ == '__main__':
    load_dotenv()
    credentials = boto3.Session(
        region_name='us-east-1',
        aws_access_key_id=getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=getenv('AWS_SECRET_ACCESS_KEY')
    ).get_credentials()
    awsauth = AWS4Auth(credentials.access_key,
                       credentials.secret_key, 'us-east-1', 'es')
    es = Elasticsearch(
        hosts=[getenv('TF_VAR_es_host')],
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        http_auth=awsauth
    )

    db = boto3.resource('dynamodb')
    MAX_BATCH_SIZE=25
    data = read_data('restaurants.json')
    print("Writing data to Dynamo DB...")
    batch_write2db(data, db)
    print("Done with Dynamo DB...")
    print("Writing data to OpenSearch...")
    batch_write2opensearch(data, es)
    print("Done with OpenSearch...")
    print("Check data inside Opensearch")
    check_opensearch_data(es)
