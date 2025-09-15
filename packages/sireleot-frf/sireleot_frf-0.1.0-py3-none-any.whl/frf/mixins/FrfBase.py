import abc
from typing import Type

from fastapi import APIRouter
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from src.frf.database.ModelBase import ModelBase


class FrfBase(abc.ABC):
    lookup_field: str
    model: Type[ModelBase]

    def __init__(self, app: str):
        self.app = app

    def get_router(self) -> APIRouter:
        router = APIRouter()
        router.add_api_route(f"{self.app}/{{id}}/", self.get_view, methods=['GET'])
        router.add_api_route(f"{self.app}/", self.list_view, methods=['GET'])
        router.add_api_route(f"{self.app}/", self.create_view, methods=['POST'])
        router.add_api_route(f"{self.app}/{{id}}/", self.update_view, methods=['PUT'])
        router.add_api_route(f"{self.app}/{{id}}/", self.partially_update_view, methods=['PATCH'])

        return router

    async def get_view(self, request: Request,  id: int) -> Response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    async def list_view(self, request: Request) -> Response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    async def create_view(self, request: Request) -> Response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    async def update_view(self) -> Response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    async def partially_update_view(self, request: Request,  id: int) -> Response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    async def delete_view(self, request: Request,  id: int) -> Response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
