# revengai.DefaultApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_analysis_function_map**](DefaultApi.md#get_analysis_function_map) | **GET** /v2/analyses/{analysis_id}/func_maps | Get Analysis Function Map


# **get_analysis_function_map**
> BaseResponseAnalysisFunctionMapping get_analysis_function_map(analysis_id, authorization=authorization)

Get Analysis Function Map

Returns the a map of function ids to function addresses for the analysis, and it's inverse.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_analysis_function_mapping import BaseResponseAnalysisFunctionMapping
from revengai.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.reveng.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = revengai.Configuration(
    host = "https://api.reveng.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKey
configuration.api_key['APIKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKey'] = 'Bearer'

# Enter a context with an instance of the API client
with revengai.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = revengai.DefaultApi(api_client)
    analysis_id = 56 # int | 
    authorization = 'authorization_example' # str | API Key bearer token (optional)

    try:
        # Get Analysis Function Map
        api_response = api_instance.get_analysis_function_map(analysis_id, authorization=authorization)
        print("The response of DefaultApi->get_analysis_function_map:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_analysis_function_map: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **authorization** | **str**| API Key bearer token | [optional] 

### Return type

[**BaseResponseAnalysisFunctionMapping**](BaseResponseAnalysisFunctionMapping.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

