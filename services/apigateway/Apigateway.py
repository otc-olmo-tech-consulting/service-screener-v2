import boto3
import botocore
import requests

from utils.Config import Config
from services.Service import Service
from services.apigateway.drivers.ApiGatewayCommon import ApiGatewayCommon
from services.apigateway.drivers.ApiGatewayRest import ApiGatewayRest

from utils.Tools import _pi

class Apigateway(Service):
   
   
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto

        self.apis = []
        self.apisv2 = []
        
        self.apiClient = ssBoto.client('apigateway', config=self.bConfig)
        self.apiv2Client = ssBoto.client('apigatewayv2', config=self.bConfig)
        self.cloudwatchClient = ssBoto.client('cloudwatch', config=self.bConfig)
        
        return
    
    def getRestApis(self):
        apis = []   

        try:
            apis = self.apiClient.get_rest_apis()
            self.apis = apis.get('items')
            while apis.get('position') is not None:
                apis = self.apiClient.get_rest_apis(position=apis.get('position'))
                self.apis = self.apis + apis.get('items')

        except botocore.exceptions.ClientError as e:
            ecode = e.response['Error']['Code']
    
    def getApis(self):
        apis = []

        try:
            apis = self.apiv2Client.get_apis()
            self.apisv2 = apis.get('Items')
            while apis.get('position') is not None:
                apis = self.apiv2Client.get_apis(position=apis.get('position'))
                self.apisv2 = self.apisv2 + apis.get('Items')

        except botocore.exceptions.ClientError as e:
            ecode = e.response['Error']['Code']
            
    def advise(self):
        try:
            objs = {}
            self.getApis()
            for api in self.apisv2:
                try:
                    objName = api.get('ProtocolType', 'UNKNOWN_PROTOCOL') + '::' + api.get('Name', api.get('ApiId', 'NO_NAME_NO_APIID'))
                    _pi('APIGateway', objName)
                    obj = ApiGatewayCommon(api, self.apiv2Client)
                    obj.run(self.__class__)
                    objs[objName] = obj.getInfo()
                    del obj
                except Exception as e:
                    # Log warning for individual API failures but continue scanning
                    api_id = api.get('ApiId', 'unknown')
                    print(f"[WARNING] Failed to process API Gateway v2 API {api_id}: {str(e)}")
                    continue

            self.getRestApis()
            for api in self.apis:
                try:
                    objName = 'REST' + '::' + api['name']
                    _pi('APIGateway', objName)
                    obj = ApiGatewayRest(api, self.apiClient)
                    obj.run(self.__class__)
                    objs[objName] = obj.getInfo()
                    del obj
                except Exception as e:
                    # Log warning for individual API failures but continue scanning
                    api_name = api.get('name', 'unknown')
                    print(f"[WARNING] Failed to process API Gateway REST API {api_name}: {str(e)}")
                    continue
        
            return objs
        
        except botocore.exceptions.ClientError as e:
            ecode = e.response['Error']['Code']
            print(ecode)