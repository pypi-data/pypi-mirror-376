import json
import re
from typing import Annotated, Union, Tuple, Optional, Dict, Any, List

from pydantic import validate_call, StrictInt, Field, StrictFloat, StrictStr

from openapi_client import SamplesApi, ApiException
from openapi_client.api_client import RequestSerialized


class SamplesApiExtension(SamplesApi):

    def __init__(self, api_client=None) -> None:
        super().__init__(api_client)

    @validate_call
    def list_sample_by_type(
        self,
        sample_type_id: Annotated[StrictInt, Field(description="sample type")],
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> List[Dict[str, int]]:

        _param = self._list_sample_serialize(
            sample_type_id=sample_type_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "SampleResponse",
            '403': "ForbiddenResponse",
            '404': "NotFoundResponse",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        if response_data.status != 200:
            match = None
            content_type = response_data.getheader('content-type')
            if content_type is not None:
                match = re.search(r"charset=([a-zA-Z\-\d]+)[\s;]?", content_type)
            encoding = match.group(1) if match else "utf-8"
            response_text = response_data.data.decode(encoding)
            raise ApiException.from_response(
                    http_resp=response_data,
                    body=response_text,
                    data=None,
                )
        my_payload = json.loads(response_data.data)['data']
        return [{str(sp['attributes']['title']): int(sp['id'])} for sp in my_payload]


    def _list_sample_serialize(
        self,
        sample_type_id,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {
        }

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[
            str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]
        ] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        # process the query parameters
        if sample_type_id is not None:
            _query_params = [('sample_type_id', sample_type_id)]

        # process the header parameters
        # process the form parameters
        # process the body parameter


        # set the HTTP header `Accept`
        if 'Accept' not in _header_params:
            _header_params['Accept'] = self.api_client.select_header_accept(
                [
                    'application/json'
                ]
            )


        # authentication setting
        _auth_settings: List[str] = [
            'OAuth2',
            'apiToken',
            'basicAuth'
        ]

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/samples',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )