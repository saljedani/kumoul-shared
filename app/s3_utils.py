import boto3
from uuid import uuid4
from flask import current_app
from botocore.client import Config


def get_s3():
    return boto3.client(
        "s3",
        region_name=current_app.config["AWS_REGION"],
        aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
        endpoint_url=f"https://s3.{current_app.config['AWS_REGION']}.amazonaws.com",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"}
        )
    )

def upload_file(file):
    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
    key = f"{uuid4().hex}.{ext}" if ext else uuid4().hex

    get_s3().upload_fileobj(
        file,
        current_app.config["AWS_BUCKET_NAME"],
        key,
        ExtraArgs={
            "ContentType": file.content_type
        }
    )

    return key


def get_url(key):
    return get_s3().generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": current_app.config["AWS_BUCKET_NAME"],
            "Key": key
        },
        ExpiresIn=3600
    )


def delete_file(key):
    return get_s3().delete_object(
        Bucket=current_app.config["AWS_BUCKET_NAME"],
        Key=key
    )