import os
import uuid
import email
import json
import urllib.parse
import boto3

s3 = boto3.client("s3")

def get_s3_email(event):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        email_object = s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
        return email.message_from_string(email_object)
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

def get_email_metadata(email_data):
    email_data = email.message_from_string(email_data)

def send_ses_email(sender_address, recipient_address, email_contents):
    ses = boto3.client("ses")
    ses.send_email(
        Destination={
            'ToAddresses': [
                recipient_address
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': 'UTF-8',
                    'Data': '<h1>Hello World</h1><p>This is a pretty mail with HTML formatting</p>',
                },
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': 'This is for those who cannot read HTML.',
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': 'Hello World',
            },
        },
        Source=sender_address
    )

def lambda_handler(event, context):
    email_data = get_s3_email(event)
    