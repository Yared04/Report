from django.contrib import admin
from .models import Database, Node, Query

# Register your models here.


@admin.register(Database)
class DatabaseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "host",
        "port",
        "database",
        "organization",
    )  # Fields to display
    list_filter = ("organization",)  # Add filters for organization
    search_fields = ("name", "description", "host", "database")  # Enable search


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "database", "parent")  # Fields to display
    list_filter = ("database", "parent")  # Add filters for database
    search_fields = ("name", "description")  # Enable search


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "database", "node")  # Fields to display
    list_filter = ("database", "node")  # Add filters for database, node
    search_fields = ("name", "description", "sql_query")  # Enable search
    readonly_fields = ("sql_query",)  # make sql query read only


admin.site.site_title = "Report management admin"
admin.site.site_header = "Report management admin dashboard"
admin.site.index_title = "Report management"
