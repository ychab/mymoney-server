from rest_framework.pagination import LimitOffsetPagination


class MyMoneyLimitOffsetPagination(LimitOffsetPagination):
    max_limit = 500
