from rest_framework.exceptions import APIException

class QueryLangException(APIException):
    status_code = 403
    default_detail = "Forbidden query"
    default_code = 'forbidden_query'