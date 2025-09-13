import logging

from django.http import StreamingHttpResponse
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import mixins
from rest_framework import viewsets, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet
from rest_framework_csv import renderers as r

from devworks_drf.form_field_errors import form_errors
from devworks_drf.pagination import SearchResultsSetPagination


log = logging.getLogger(__name__)


class BasicViewSetActions:

    def list(self, request, **kwargs):
        return super().list(request, **kwargs)

    def retrieve(self, request, pk=None, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response = Response(
            {
                "success": True,
                "result": serializer.data
            }
        )
        return response

    def create(self, request, refresh_serializer=False, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": form_errors(serializer.errors)},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        if refresh_serializer:
            instance = serializer.instance
            serializer = self.get_serializer(instance)
        headers = self.get_success_headers(serializer.data)
        if hasattr(self, "on_success_modify"):
            self.on_success_modify(
                serializer.instance,
                action='create'
            )

        response = Response(
            {"success": True, "result": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
        return response

    def update(self, request, *args, data=None, refresh_serializer=False, **kwargs):
        data = data if data is not None else request.data
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=data,
            partial=partial
        )
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": form_errors(serializer.errors)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        if refresh_serializer:
            instance = serializer.instance
            serializer = self.get_serializer(instance)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        if hasattr(self, "on_success_modify"):
            self.on_success_modify(
                serializer.instance,
                action='update'
            )
        response = Response(
            {
                "success": True,
                "result": serializer.data
            }
        )
        return response

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, pk=None, **kwargs):
        instance = self.get_object()

        if hasattr(self, "on_success_modify"):
            self.on_success_modify(instance, action="delete")

        instance.delete()

        response = Response({"success": True, "result": {}})
        return response


class CommonViewSet(BasicViewSetActions, viewsets.ModelViewSet):
    pagination_class = SearchResultsSetPagination


class WriteableNestedViewSet(
    BasicViewSetActions,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    pass


class SearchViewSet(ReadOnlyModelViewSet):
    pagination_class = SearchResultsSetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.CSVStreamingRenderer,)

    mapping = []
    filter_backends = []

    def list(self, request, **kwargs):
        self._queryset = self.filter_queryset(
            self.get_queryset()
        )

        if self.request.GET.get('format') == 'csv':
            def stream():
                for csv_hits in self._queryset.scan():
                    yield csv_hits.to_dict()

            return StreamingHttpResponse(
                request.accepted_renderer.render(stream()),
                content_type='text/csv'
            )

        stats = {}
        page, hits = self.paginate_queryset(self._queryset)
        try:
            data = [h.to_dict() for h in page]
        except AttributeError:
            data = page

        if hasattr(self, "post_process_hits"):
            data = self.post_process_hits(data, aggregations=hits.aggregations)

        serializer = self.get_serializer(data, many=True)

        data = serializer.data
        return self.paginator.get_paginated_response(data, stats)

    def retrieve(self, request, pk=None, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter('term', id=pk)
        try:
            instance = queryset.execute()[0]
            if hasattr(instance, "to_dict"):
                instance = instance.to_dict()
        except IndexError:
            return Response({"success": None}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(self, "post_process_hits"):
            # _data = [instance.to_dict()]
            print("CSDJANGO.post_process_hits: instance", instance)
            post_process = self.post_process_hits([instance])
            print("CSDJANGO.post_process_hits: post_process", post_process)
            data = post_process[0]
        else:
            data = instance
        serializer = self.get_serializer(data)

        return Response({"success": True, "result": serializer.data})


class SearchWriteNestedViewSet(SearchViewSet, WriteableNestedViewSet):
    model = None
    queryset = None
    serializer_class = None
    document = None

    @property
    def action_object_name(self):
        if self.action in ('list', 'retrieve'):
            return 'elasticsearch'
        return 'model'

    def get_queryset(self):
        return super(SearchViewSet, self).get_queryset()

    def get_object(self):
        # object is always model ...
        #  except on retrieve which is overwritten in `SearchViewSet`
        elastic_queryset = super(SearchViewSet, self).get_queryset()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {"id": self.kwargs[lookup_url_kwarg]}
        try:
            objs = elastic_queryset.filter('term', **filter_kwargs).execute()
            obj = objs[0]
        except IndexError:
            raise NotFound()
        return self.model.objects.get(id=obj.id)
