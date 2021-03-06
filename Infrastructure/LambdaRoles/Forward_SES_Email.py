import os
import uuid
import email
import json
import urllib.parse
import boto3

"""
ref for some of the code used here https://blog.bytefaction.com/posts/setup-custom-private-email-relay-part1/
"""

s3 = boto3.client("s3")

def get_s3_email(event):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        email_object = s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
        return email.message.Message.message_from_string(email_object)
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

def generate_sender_address(from_addresses, sender_suffix):
    """
    From https://blog.bytefaction.com/posts/setup-custom-private-email-relay-part1/
    """
    split_arr = from_addresses.split()
    from_email = split_arr.pop()
    from_name = None
    if len(split_arr) > 0:
        from_name = " ".join(split_arr)
    from_email = from_email.replace('@', '_at_')
    from_email = from_email.replace('.', '_dot_')
    from_email = from_email.replace('+', '_plus_')
    from_email = from_email + '_' + sender_suffix
    if from_name:
        return from_name + ' <' + from_email + '>'
    else:
        return from_email

def get_email_metadata(email_object):
    separator = ";"
    
    from_list = separator.join(email_object.get_all('From'))
    from_list = from_list.replace('<', '')
    from_list = from_list.replace('>', '')
    to_address = separator.join(email_object.get_all('To'))
    to_address = to_address.replace('<', '')
    to_address = to_address.replace('>', '')
    msg = email.mime.multipart.MIMEMultipart()

    if email_object.is_multipart():
        for payload in email_object.get_payload():
            if payload.is_multipart():
                body = email_object.get_body()
            if payload.get_content_type() == "text/plain":
                body = payload.get_payload()
    else:
        body = email_object.get_payload()

    msg['Subject'] = email_object['Subject']
    msg['From'] = generate_sender_address(from_list, to_address.replace(' ', '_'))
    msg['To'] = 'jsm.moorman@outlook.com'

    message = {
        "Source": msg["From"],
        "Destinations": msg['To'],
        "Data": msg.as_string()
    }

    return message



def send_ses_email(message):
    ses = boto3.client("ses")

    try:
        response = ses.send_raw_email(
            Source = message["Source"],
            Destinations = message['Destinations'],
            RawMessage = {
                'Data': message['Data']
            }
        )
    except ClientError as e:
        return e.response['Error']['Message']
    else:
        return "Email sent! Message ID: " + response['MessageId']

def lambda_handler(event, context):
    email_data = get_s3_email(event)
    
    