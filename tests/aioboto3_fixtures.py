"""
AWS asyncio test fixtures
"""
from typing import Any, AsyncIterator, Dict, Iterator, List, Type, TypeVar
from unittest import mock

import aioboto3
import boto3
import pytest
from types_aiobotocore_s3 import S3Client

from .moto_fixtures import MockedAWSService

T = TypeVar("T")


def create_fake_session(base_class: Type[T], url_overrides: Dict[str, str]) -> Type[T]:
    class FakeSession(base_class):  # type:ignore[valid-type, misc]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super(FakeSession, self).__init__(*args, **kwargs)

            self.__url_overrides = url_overrides
            self.__secret_key = "ABCDEFGABCDEFGABCDEF"
            self.__access_key = "YTYHRSshtrsTRHSrsTHRSTrthSRThsrTHsr"

        def client(self, *args: Any, **kwargs: Any) -> Any:

            if "endpoint_url" not in kwargs and args[0] in self.__url_overrides:
                kwargs["endpoint_url"] = self.__url_overrides[args[0]]

            kwargs["aws_access_key_id"] = self.__secret_key
            kwargs["aws_secret_access_key"] = self.__access_key

            return super(FakeSession, self).client(*args, **kwargs)

        def resource(self, *args: Any, **kwargs: Any) -> Any:

            if "endpoint_url" not in kwargs and args[0] in self.__url_overrides:
                kwargs["endpoint_url"] = self.__url_overrides[args[0]]

            kwargs["aws_access_key_id"] = self.__secret_key
            kwargs["aws_secret_access_key"] = self.__access_key

            return super(FakeSession, self).resource(*args, **kwargs)

    return FakeSession


@pytest.fixture
def moto_patch_session(moto_services: List[MockedAWSService]) -> Iterator[None]:
    services_map = {service.service_name: service.moto_url for service in moto_services}
    MotoAioboto3Session = create_fake_session(aioboto3.Session, services_map)
    MotoBoto3Session = create_fake_session(
        boto3.Session,
        services_map,
    )

    sessions = [
        mock.patch("aioboto3.Session", MotoAioboto3Session),
        mock.patch("aioboto3.session.Session", MotoAioboto3Session),
        mock.patch("boto3.Session", MotoBoto3Session),
        mock.patch("boto3.session.Session", MotoBoto3Session),
    ]
    for session in sessions:
        session.start()

    yield

    for session in sessions:
        session.stop()


@pytest.fixture
async def aioboto3_s3_client(moto_patch_session: None) -> AsyncIterator[S3Client]:
    session = aioboto3.Session(region_name="us-east-1")
    async with session.client("s3", region_name="us-east-1") as client:  # type: S3Client
        yield client
