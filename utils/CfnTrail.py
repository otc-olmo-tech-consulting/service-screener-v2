import uuid
import sys

import boto3
import botocore
from botocore.config import Config as bConfig

from utils.Config import Config
from utils.Tools import _warn, _info

## Class name decided by Sarika
class CfnTrail():
    additionalDesc = None
    def __init__(self):
        self.stackName = None
        self.cfnTemplate = "zNullResourcesCfn.yml"
        self.stackPrefix = "ssv2-"
        self.defaultRegion = "us-east-1"
        self.ymlBody='''
AWSTemplateFormatVersion: '2010-09-09'
Description: '[aws-gh-ss-v2] Service Screener V2{}'

Conditions:
  HasNot: !Equals [ 'true', 'false' ]
 
# dummy (null) resource, never created
Resources:
  NullResource:
    Type: 'Custom::NullResource'
    Condition: HasNot 
'''
        self.ymlBodyOutput='''
Outputs:
  ExportsStackName:
    Value: !Ref 'AWS::StackName'
    Export:
      Name: !Sub 'ExportsStackName-${AWS::StackName}'
'''

        # self.boto3init()
        
    def boto3init(self, additionalDesc = None):
        self.bConfig = bConfig(
            region_name = self.getRegion()
        )
        
        ssBoto = Config.get('ssBoto', None)
        self.cfClient = ssBoto.client('cloudformation', config=self.bConfig)

        self.additionalDesc = additionalDesc
        
    def createStack(self):
        try:
            yml = self.ymlBody.format(self.additionalDesc) + self.ymlBodyOutput
            self.cfClient.create_stack(
                StackName=self.getStackName(),
                TemplateBody=yml
            )
            msg = "Empty CF stacked created successfully, name:" + self.getStackName()
            _info(msg, alwaysPrint=True)
        
        except botocore.exceptions.ClientError as e:
            ecode = e.response['Error']['Code']
            emsg = e.response['Error']['Message']
            print(ecode, emsg)
            print("----")
            sys.exit("Please grant cloudformation:CreateStack permission to the user and retry")
    
    def deleteStack(self):
        try:
            self.cfClient.delete_stack(
                StackName=self.getStackName()    
            )
            
            msg = "Empty CF stacked deleted successfully, name:" + self.getStackName()
            _info(msg, alwaysPrint=True)
        except botocore.exceptions.ClientError as e:
            ecode = e.response['Error']['Code']
            emsg = e.response['Error']['Message']
            print(ecode, emsg)
            print("Unable to delete CF stack. Although no cost will be incur, recommend to clean up the stack for hygiene purposes")
    
    def getStackName(self):
        if self.stackName == None:
            self.stackName = self.stackPrefix + uuid.uuid4().hex[0:12]
        
        return self.stackName
    
    def getRegion(self):
        """
        Always use us-east-1 for the audit trail CF stack.
        
        The CF stack is an empty marker for audit purposes only — it doesn't 
        need to be in the same region being scanned. Using a fixed region 
        avoids permission issues when clients scan newer/opt-in regions 
        (e.g., mx-central-1) where their IAM policies may not yet grant 
        cloudformation:CreateStack.
        """
        return self.defaultRegion