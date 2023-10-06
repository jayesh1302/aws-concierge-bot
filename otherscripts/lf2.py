import boto3


def lambda_handler(event, context):
    result = "Hello World from lf2!"
    return {
        'statusCode': 200,
        'body': result
    }
