import boto3
import os
import json
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
client_table = dynamodb.Table(os.environ['CLIENT_TABLE'])
apigatewaymanagementapi = boto3.client(
    'apigatewaymanagementapi', endpoint_url=os.environ['WEBSOCKET_API'],)


def handler(event, context):
    requestContext = event['requestContext']
    eventType = requestContext['eventType']
    connectionId = requestContext['connectionId']

    if eventType == 'CONNECT':
        role = event['queryStringParameters']['role']
        try:
            if role == 'board':
                client_table.put_item(
                    Item={
                        'id': connectionId
                    }
                )
                return {
                    "statusCode": 200,
                    "body": "Scoreboard connected"
                }
            elif role == 'submitter':
                return {
                    "statusCode": 200,
                    "body": "Submitter connected"
                }

        except Exception as e:
            print(e)
            return {
                "statusCode": 500,
                "body": "Internal Server Error"
            }

    elif eventType == 'DISCONNECT':
        try:
            client_table.delete_item(
                Key={
                    'id': connectionId
                },
            )
            return {
                "statusCode": 200,
                "body": "Disconnected"
            }
        except Exception as e:
            print(e)
            return {
                "statusCode": 500,
                "body": "Internal Server Error"
            }
