import django_filters
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..utils import TastypiePagination


class BaseView(APIView):
    permission_classes = (IsAuthenticated,)  # by default all users must be authenticated
    serializer_class = None  # overridden for each subclass
    queryset = None  # override to provide queryset for list and detail views

    # configure filtering of list endpoints by query string
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,  # subclasses can be filtered by keyword if filterset_class is set
        SearchFilter,  # subclasses can be filtered by q= if search_fields is set
        OrderingFilter  # subclasses can be ordered by order_by= if ordering_fields is set
    )
    ordering_fields = ()  # lock down order_by fields -- security risk if unlimited

    ### helpers ###

    def get_queryset(self, queryset=None):
        """
        Return queryset, or self.queryset, or raise config error.
        """
        if queryset is None:
            if self.queryset is None:
                raise NotImplementedError("No queryset configured on subclass.")
            queryset = self.queryset
        return queryset

    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.
        Copied from GenericAPIView.
        """
        try:
            for backend in list(self.filter_backends):
                queryset = backend().filter_queryset(self.request, queryset, self)
            return queryset
        except DjangoValidationError as e:
            raise ValidationError(e.error_dict)

    def get_object_for_user(self, user, queryset):
        """
        Get single object from queryset, making sure that returned object is accessible_to(user).
        """
        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404
        if not obj.accessible_to(user):
            raise PermissionDenied()
        return obj

    def get_object_for_user_by_pk(self, user, pk):
        """
        Get single object by primary key, based on our serializer_class.
        """
        queryset = self.queryset.all() if self.queryset is not None else self.serializer_class.Meta.model.objects.all()
        return self.get_object_for_user(user, queryset.filter(pk=pk))

    ### basic views ###
    
    def simple_list(self, request, queryset=None, serializer_class=None, paginator_class=None):
        """
        Paginate and return a list of objects from given queryset.
        """
        queryset = self.get_queryset(queryset)
        queryset = self.filter_queryset(queryset)
        paginator = paginator_class() if paginator_class else TastypiePagination()
        items = paginator.paginate_queryset(queryset, request)
        serializer_class = serializer_class if serializer_class else self.serializer_class
        serializer = serializer_class(items, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def simple_get(self, request, pk=None, obj=None, serializer_class=None):
        """
        Return single serialized object based on either primary key or object already loaded.
        """
        if not obj:
            obj = self.get_object_for_user_by_pk(request.user, pk)
        serializer_class = serializer_class if serializer_class else self.serializer_class
        serializer = serializer_class(obj, context={"request": request})
        return Response(serializer.data)

    def simple_create(self, data, save_kwargs={}):
        """
        Validate and save new object.
        """
        serializer = self.serializer_class(data=data, context={"request": self.request})
        if serializer.is_valid():
            serializer.save(**save_kwargs)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def simple_update(self, obj, data):
        """
        Validate and update given fields on object.
        """
        serializer = self.serializer_class(obj, data=data, partial=True, context={"request": self.request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        raise ValidationError(serializer.errors)

    def simple_delete(self, obj):
        """
        Delete object.
        """
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
