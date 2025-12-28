import boto3
sts = boto3.client('sts')
identity = sts.get_caller_identity()
print(f"Current AWS Identity:")
print(f"  User/Role: {identity['Arn']}")
print(f"  Account: {identity['Account']}")
