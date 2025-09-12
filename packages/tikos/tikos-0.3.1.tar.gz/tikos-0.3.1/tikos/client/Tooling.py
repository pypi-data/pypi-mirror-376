import json
from typing import Any, List, Tuple
import concurrent.futures
import requests
import base64

from tikos.config import VER, BASE_URL_API

class Tooling(object):

    def __init__(self, url: str = "", requestId: str = "", authToken: str = ""):
        if url == "":
            self.url = BASE_URL_API
        else:
            self.url = url
        self.requestId = requestId
        self.authToken = authToken

    '''
        Foundational Model Profiling Matching tool
        Accepts: PayloadId, Reference Docs, Case-Type, Network Type, Reasoning Type, Similarity Type, NMP model Type, Payload Config, Network Type, Model Name, Prompt List and the Token Length
    '''
    # Reasoning:Base
    def __GetProfileMatchingBase(self, url: str = "", requestId: str = "", authToken: str = "", payloadId: str = "", refdoc: str = "", refCaseType: str = "", RType: str = "", WType: str = "", llmmodel: int = 2, payloadconfig: str = "", nType: int = 0,
                           modelName: str = "", promptTextList: List[str] = [], tokenLen:int = 100):
        if url == "":
            url = BASE_URL_API

        result = requests.post(url + '/tooling/profiling',
                               json={'requestId': requestId, 'authToken': authToken, 'payloadId': payloadId, 'refdoc': refdoc,
                                     'refCaseType': refCaseType, 'RType': RType, 'WType': WType, 'X-TIKOS-MODEL': llmmodel, 'payloadconfig': payloadconfig,
                                     'nType': nType, 'modelName': modelName, 'promptTextList': promptTextList, 'tokenLen': tokenLen})
        return result.status_code, result.reason, result.text

    def generateFMProfileMatching(self, payloadId: str = "", refdoc: str = "", refCaseType: str = "", RType: str = "DEEPCAUSAL_PROFILE_PATTERN_ADV", WType: str = "PROFILING", llmmodel: int = 2, payloadconfig: str = "", nType: int = 2,
                           modelName: str = "meta-llama/Llama-3.2-1B", promptTextList: List[str] = [], tokenLen:int = 100):

        rtnVal = self.__GetProfileMatchingBase(
            url=self.url,
            requestId=self.requestId,
            authToken=self.authToken,
            payloadId=payloadId,
            refdoc=refdoc,
            refCaseType=refCaseType,
            RType=RType,
            WType=WType,
            llmmodel=llmmodel,
            payloadconfig=payloadconfig,
            nType=nType,
            modelName=modelName,
            promptTextList=promptTextList,
            tokenLen=tokenLen,
        )

        return rtnVal

    '''
        Foundational Model Profiling Guard Railing tool
        Accepts: PayloadId, Reference Docs, Case-Type, Network Type, Reasoning Type, Similarity Type, NMP model Type, Payload Config, Network Type, Model Name, Prompt List and the Token Length
    '''
    # Reasoning:Base
    def __GetProfileGuardRailingBase(self, url: str = "", requestId: str = "", authToken: str = "", payloadId: str = "",
                                 refdoc: str = "", refCaseType: str = "", RType: str = "", WType: str = "",
                                 llmmodel: int = 2, payloadconfig: str = "", nType: int = 0,
                                 modelName: str = "", promptTextList: List[str] = [], tokenLen: int = 100):
        if url == "":
            url = BASE_URL_API

        result = requests.post(url + '/tooling/profiling/guardrailing',
                               json={'requestId': requestId, 'authToken': authToken, 'payloadId': payloadId,
                                     'refdoc': refdoc,
                                     'refCaseType': refCaseType, 'RType': RType, 'WType': WType,
                                     'X-TIKOS-MODEL': llmmodel, 'payloadconfig': payloadconfig,
                                     'nType': nType, 'modelName': modelName, 'promptTextList': promptTextList,
                                     'tokenLen': tokenLen})
        return result.status_code, result.reason, result.text

    def generateFMProfileGuardRailing(self, payloadId: str = "", refdoc: str = "", refCaseType: str = "", RType: str = "DEEPCAUSAL_PROFILE_PATTERN_ADV", WType: str = "PROFILING", llmmodel: int = 2, payloadconfig: str = "", nType: int = 2,
                           modelName: str = "meta-llama/Llama-3.2-1B", promptTextList: List[str] = [], tokenLen:int = 100):

        rtnVal = self.__GetProfileGuardRailingBase(
            url=self.url,
            requestId=self.requestId,
            authToken=self.authToken,
            payloadId=payloadId,
            refdoc=refdoc,
            refCaseType=refCaseType,
            RType=RType,
            WType=WType,
            llmmodel=llmmodel,
            payloadconfig=payloadconfig,
            nType=nType,
            modelName=modelName,
            promptTextList=promptTextList,
            tokenLen=tokenLen,
        )

        return rtnVal

    '''
        Deep learning model robustness analysis tool
        Accepts: JSON payload string 
        {
            "models": [
                {
                    "model_name": "Model 1",
                    "case_type": "iris flowers",
                    "target": "species",
                    "org_id": "tikos",
                    "input_features": [
                        "sepal_length",
                        "sepal_width",
                        "petal_length",
                        "petal_width"
                    ],
                    "session": {
                        "requestId": "tikos",
                        "authToken": "tikos"
                    },
                    "model_size": 000,
                    "test_data_filename": "file.csv"
                }
            ]
        }
    '''
    # Model Robustness:Base
    def __analyseModelRobustness(self, url: str = "", payloadJsonStr: str = ""):
        if url == "":
            url = BASE_URL_API

        jsonPayload= json.dumps(payloadJsonStr)

        uploadFiles = {
            'json': ('payload.json', jsonPayload, 'application/json')
        }

        result = requests.post(url + '/tooling/modelrobustness',files=uploadFiles)

        return result.status_code, result.reason, result.text

    def analyseModelRobustness(self, payloadJsonStr: str = ""):

        rtnVal = self.__analyseModelRobustness(
            url=self.url,
            payloadJsonStr=payloadJsonStr)

        return rtnVal


    '''
        Deep learning model Feature Association analysis tool
        Accepts: JSON payload string
        eg: 
        {
            "visualizing_info": {
                "case_type": "cancer_type",
                "target": "net_survival",
                "org_id": "tikos",
                "input_features": [
                    "cancer_type",
                    "survival_type",
                    "stage",
                    "age_group",
                    "sex",
                    "survival_time_years",
                    "number_of_patients"
                ],
                "session": {
                    "requestId": "tikos",
                    "authToken": "tikos"
                },
                "test_data_filename": "file.csv"
            }
        }
    '''
    # Model Feature Association:Base
    def __analyseModelFeatureAssociation(self, url: str = "", payloadJsonStr: str = ""):
        if url == "":
            url = BASE_URL_API

        jsonPayload = json.dumps(payloadJsonStr)

        uploadFiles = {
            'json': ('payload.json', jsonPayload, 'application/json')
        }

        result = requests.post(url + '/tooling/featureassociation', files=uploadFiles)

        return result.status_code, result.reason, result.text

    def analyseModelFeatureAssociation(self, payloadJsonStr: str = ""):

        rtnVal = self.__analyseModelRobustness(
            url=self.url,
            payloadJsonStr=payloadJsonStr)

        return rtnVal

    def analyseModelFeatureAssociationSerialised(self, payloadJsonStr: str = ""):

        statusCode, statusReason, rtnText = self.__analyseModelRobustness(
            url=self.url,
            payloadJsonStr=payloadJsonStr)

        if statusCode == 200:
            jsonLoad = json.loads(rtnText)
            rtnLst = []

            for i, viz in enumerate(jsonLoad.get("visualizations", [])):
                print(f"  Title: {viz.get('title')}")
                base64_string = viz.get('image_base64')
                if base64_string:
                    image_bytes = base64.b64decode(base64_string)

                    filename = f"{viz.get('title', f'image_{i + 1}').replace(' ', '_')}.png"
                    rtnLst.append((filename, image_bytes))
                else:
                    print(" No image data found for this visualization.")

            return rtnLst
        else:
            return None