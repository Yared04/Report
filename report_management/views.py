from django.shortcuts import render
from report_management.permissions import IsOrganizationAdmin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Database, Node, Query
from report_management.serializers import NodeSerializer, QuerySerializer, DatabaseSerializer  # Import the serializers
# Create your views here.


class DatabaseView(APIView):
    """
    View to manage database connections.
    """

    permission_classes = [IsOrganizationAdmin]

    def get(self, request):
        """
        List all database connections.
        """
        databases = Database.objects.all()
        serializer = DatabaseSerializer(databases, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new database connection.
        """
        serializer = DatabaseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class NodeView(APIView):
    """
    View to manage nodes.
    """

    permission_classes = [IsOrganizationAdmin]

    def get(self, request):
        """
        List all nodes.
        """
        nodes = Node.objects.all()
        serializer = NodeSerializer(nodes, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new node.
        """
        serializer = NodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class QueryView(APIView):
    """
    View to manage queries.
    """

    permission_classes = [IsOrganizationAdmin]

    def get(self, request):
        """
        List all queries.
        """
        queries = Query.objects.all()
        serializer = QuerySerializer(queries, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new query.
        """
        serializer = QuerySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)