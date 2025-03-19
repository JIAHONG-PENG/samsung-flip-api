import boto3
import json
from datetime import datetime
import os

dynamodb = boto3.resource("dynamodb")
client_table = dynamodb.Table(os.environ['CLIENT_TABLE'])
score_table = dynamodb.Table(os.environ['SCORE_TABLE'])
rank_table = dynamodb.Table(os.environ['RANK_TABLE'])
apigatewaymanagementapi = boto3.client(
    'apigatewaymanagementapi', endpoint_url=os.environ['WEBSOCKET_API'],)


def handler(event, context):
    print(event)
    data = json.loads(event['body'])['body']
    name = data['name']
    time = int(data['time'])
    mobile = data['mobile']

    try:
        score_table.put_item(
            Item={
                'mobile': mobile,
                'name': name,
                'time': time,
                'submitTime': str(datetime.now()),
            }
        )

        # check mobile exist in ranke table
        res = rank_table.get_item(Key={'mobile': mobile})

        putInRankTable = False
        if 'Item' in res:
            if time < int(res['Item']['time']):
                putInRankTable = True
            else:
                return {
                    "statusCode": 200,
                    "body": "Updated"
                }
        else:
            putInRankTable = True

        rank_res = rank_table.scan(
            IndexName=os.environ['RANK_INDEX'],
            Limit=20,
            ProjectionExpression='#name, #time, #mobile, #submitTime',
            ExpressionAttributeNames={
                '#name': 'name', '#time': 'time', '#mobile': 'mobile', '#submitTime': "submitTime"}
        )['Items']

        rank_res_sorted = sorted(rank_res, key=lambda x: (
            int(x['time']), datetime.strptime(x['submitTime'], '%Y-%m-%d %H:%M:%S.%f')))

        top10 = rank_res_sorted[0:10]

        if putInRankTable:
            rank_table.put_item(
                Item={
                    'mobile': mobile,
                    'name': name,
                    'time': time,
                    'submitTime': str(datetime.now()),
                    'prefix': 'prefix',
                }
            )

        connections = client_table.scan(ProjectionExpression='id')['Items']

        inTop10 = False
        sendToClient = False
        for record in top10:
            if record['mobile'] == mobile:
                inTop10 = True
                if time < int(record['time']):
                    sendToClient = True
                break

        if not inTop10:
            if len(top10) < 10:
                sendToClient = True
            elif time < int(top10[-1]['time']):
                sendToClient = True

        if sendToClient:
            for connection in connections:
                apigatewaymanagementapi.post_to_connection(
                    ConnectionId=connection['id'],
                    Data=json.dumps({
                        'type': 'update',
                        'body': {'name': name, 'time': time, 'mobile': mobile}
                    })
                )

        return {
            "statusCode": 200,
            "body": "Updated"
        }
    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "body": "Internal Server Error"
        }
