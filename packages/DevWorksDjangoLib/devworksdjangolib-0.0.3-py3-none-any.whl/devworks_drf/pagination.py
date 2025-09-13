import contextlib
from math import ceil

from rest_framework.pagination import PageNumberPagination, _positive_int
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param


class CommonPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    page_size = 16
    max_page_size = 1000

    def get_page_size(self, request):
        if self.page_size_query_param:
            with contextlib.suppress(KeyError, ValueError):
                if request.query_params[self.page_size_query_param] == '0':
                    return 0
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=False,
                    cutoff=self.max_page_size
                )
        return self.page_size

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request  # for later use
        page_size = self.get_page_size(request)

        if page_size:
            result = super().paginate_queryset(queryset, request, view=view)
            hits = queryset.execute()
            return result, hits
        else:
            result = queryset.extra(size=0).execute()
            return result, result

    @property
    def current_page_size(self):
        return self.get_page_size(self.request)

    def get_base_link(self):
        url = self.request.build_absolute_uri()
        return remove_query_param(url, self.page_query_param)

    def get_page_count(self):
        if not self.page.paginator.count:
            return 0
        return ceil(self.page.paginator.count / self.current_page_size)

    def get_paginated_response(self, data):
        self.page = getattr(self, 'page', 0)  # for later use
        return Response(
            {
                'success': True,
                'results': {
                    'pages': {
                        'base_url': self.get_base_link(),
                        'records': {
                            "total": self.page.paginator.count if self.page else 0,
                            "current": len(data)
                        },
                        'page': {
                            "total": self.get_page_count() if self.page else 0,
                            "current": self.page.number if self.page else 0,
                            "page_size": self.current_page_size if self.page else 0
                        }
                    },
                    'list': data
                }
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'pages': {
                    'type': 'object',
                    'properties': {
                        'base_url': {'type': 'string', 'format': 'uri'},
                        'records': {
                            'type': 'object',
                            'properties': {
                                'total': {'type': 'integer'},
                                'current': {'type': 'integer'},
                            },
                        },
                        'page': {
                            'type': 'object',
                            'properties': {
                                'total': {'type': 'integer'},
                                'current': {'type': 'integer'},
                                'page_size': {'type': 'integer'},
                            },
                        },
                    },
                },
                'list': schema,
            },
        }


class SearchResultsSetPagination(CommonPagination):

    def get_statistic_details(self, name, chunk):
        if name.startswith("_"):
            for name, chunk in chunk.items():
                if isinstance(chunk, dict):
                    yield from self.get_statistic_details(name, chunk)
                yield {name: chunk}
        else:
            yield {name: chunk}

    def get_statistics(self, stats):
        if not stats:
            return {}
        if not isinstance(stats, dict):
            stats = stats.to_dict()
        statistics = {}
        for name, chunk in stats.items():
            for processed in self.get_statistic_details(name, chunk):
                statistics.update(processed)
        return statistics

    def get_paginated_response(self, data):
        self.page = getattr(self, 'page', 0)  # for later use
        return Response(
            {
                'success': True,
                'results': {
                    'pages': {
                        'base_url': self.get_base_link(),
                        'records': {
                            "total": self.page.paginator.count if self.page else 0,
                            "current": len(data)
                        },
                        'page': {
                            "total": self.get_page_count() if self.page else 0,
                            "current": self.page.number if self.page else 0,
                            "page_size": self.current_page_size if self.page else 0
                        }

                    },
                    'list': data
                }
            }
        )


class AggregationPagination(CommonPagination):

    def get_paginated_response(self, result, stats=None):
        self.page = getattr(self, 'page', 0)  # for later use
        return Response(
            {
                'success': True,
                'results': {
                    'pages': {
                        'base_url': self.get_base_link(),
                        'records': {
                            "total": self.page.paginator.count if self.page else 0,
                            "current": len(result)
                        },
                        'page': {
                            "total": self.get_page_count() if self.page else 0,
                            "current": self.page.number if self.page else 0,
                            "page_size": self.current_page_size if self.page else 0
                        }

                    },
                    'stats': stats or {},
                    'list': result
                }
            }
        )
