import boto3
import os
from datetime import datetime
import json

dynamodb = boto3.resource("dynamodb")
rank_table = dynamodb.Table(os.environ['RANK_TABLE'])
apigatewaymanagementapi = boto3.client(
    'apigatewaymanagementapi', endpoint_url=os.environ['WEBSOCKET_API'],)


def handler(event, context):
    requestContext = event['requestContext']
    connectionId = requestContext['connectionId']

    newRecord = rank_table.scan(
        IndexName=os.environ['RANK_INDEX'],
        Limit=20,
        ProjectionExpression='#name, #time, #mobile, #submitTime',
        ExpressionAttributeNames={
            '#name': 'name', '#time': 'time', '#mobile': 'mobile', '#submitTime': 'submitTime'}
    )['Items']

    for record in newRecord:
        record['time'] = int(record['time'])

    newRecord_sorted = sorted(newRecord, key=lambda x: (
        int(x['time']), datetime.strptime(x['submitTime'], '%Y-%m-%d %H:%M:%S.%f')))

    top10 = newRecord_sorted[0:10]

    apigatewaymanagementapi.post_to_connection(
        ConnectionId=connectionId,
        Data=json.dumps({
            'type': 'init',
            'body': top10,
        })
    )

    return {
        "statusCode": 200,
        "body": ""
    }
