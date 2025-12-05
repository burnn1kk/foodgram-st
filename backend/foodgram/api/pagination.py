from rest_framework.pagination import PageNumberPagination


# не стал объединять в один класс для потенциального изменения какого-то конкретного
class PageLimitPagination(PageNumberPagination):
    page_size_query_param = "limit"
    page_query_param = "page"
    page_limit = 1


class RecipePagination(PageNumberPagination):
    page_size_query_param = "limit"
    page_query_param = "page"
    page_limit = 1


class UsersPagination(PageNumberPagination):
    page_size_query_param = "limit"
    page_query_param = "page"
    page_size = 1


class SubscriptionPagination(PageNumberPagination):
    page_size_query_param = "limit"
    page_query_param = "page"
    page_size = 1
