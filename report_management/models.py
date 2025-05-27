from django.db import models
from report.models import BaseModel

# Create your models here.


class Database(BaseModel):
    """
    Model representing a connection to a database in the report management system.
    """

    name = models.CharField(max_length=255)
    description = models.TextField()
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="databases"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Database Connection"
        verbose_name_plural = "Database Connections"
        ordering = ["name"]


class Node(BaseModel):
    """
    Model representing a node in the report management system.
    """

    name = models.CharField(max_length=255)
    description = models.TextField()
    database = models.ForeignKey(
        Database,
        on_delete=models.CASCADE,
        related_name="nodes",
        default=None,
        null=True,
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    def __str__(self):
        return self.name


class Query(BaseModel):
    """
    Model representing a query in the report management system.
    """

    name = models.CharField(max_length=255)
    description = models.TextField()
    sql_query = models.TextField()
    node = models.ForeignKey(
        Node, null=True, blank=True, on_delete=models.CASCADE, related_name="queries"
    )
    database = models.ForeignKey(
        Database, on_delete=models.CASCADE, related_name="queries"
    )

    def __str__(self):
        return self.name
