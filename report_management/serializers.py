from rest_framework import serializers
from .models import Database, Node, Query

class DatabaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Database
        fields = '__all__' # Or list specific fields: ['id', 'name', 'description', 'host', 'port', 'database', 'username', 'organization']
        read_only_fields = ('id', 'created_at', 'updated_at')
        
class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = '__all__' # Or list specific fields: ['id', 'name', 'description', 'sql_query', 'node', 'database']
        read_only_fields = ('id', 'created_at', 'updated_at')
        
class NodeSerializer(serializers.ModelSerializer):
    queries = QuerySerializer(many=True, read_only=True)

    class Meta:
        model = Node
        fields = ['id', 'name', 'description', 'parent', 'queries']
        read_only_fields = ('id', 'created_at', 'updated_at')
        
        
        
