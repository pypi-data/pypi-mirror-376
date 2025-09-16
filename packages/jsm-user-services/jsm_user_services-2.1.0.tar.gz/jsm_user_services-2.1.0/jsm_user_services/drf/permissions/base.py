from requests.exceptions import HTTPError
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from jsm_user_services import settings
from jsm_user_services.services.user import get_user_data_from_server


class JSMUserBasePermission(permissions.BasePermission):
    """
    Base class for JSM user permissions. Implements methods for validating requests against
    the user micro service so that any type of permission can be carried out (role, status, etc).
    """

    APPEND_USER_DATA = settings.JSM_USER_SERVICES_DRF_APPEND_USER_DATA
    USER_DATA_ATTR_NAME = settings.JSM_USER_SERVICES_DRF_REQUEST_USER_DATA_ATTR_NAME
    USER_SERVICE_NOT_AUTHORIZED_CODES = (401, 403, 404)

    @classmethod
    def _retrieve_user_data(cls, request: Request) -> dict:
        try:
            user_data = getattr(request, cls.USER_DATA_ATTR_NAME)
        except AttributeError:
            user_data = get_user_data_from_server()

        return user_data

    @classmethod
    def _validate_request_against_user_service(cls, request: Request, append_user_data_to_request: bool = True) -> dict:
        """
        Gets valid user_data from the User micro service.
        """
        if not settings.JSM_USER_SERVICE_REQUEST_USER_DATA:
            return {}

        try:
            user_data: dict = cls._retrieve_user_data(request)

            if append_user_data_to_request:
                setattr(request, cls.USER_DATA_ATTR_NAME, user_data)

        except HTTPError as e:
            if e.response.status_code in cls.USER_SERVICE_NOT_AUTHORIZED_CODES:
                return {}

            raise

        return user_data

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Abstract method that must be implemented by children classes.
        """
        raise NotImplementedError("This method must be overridden!")
