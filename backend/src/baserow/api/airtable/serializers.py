from rest_framework import serializers

from baserow.contrib.database.airtable.models import AirtableImportJob


class AirtableImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirtableImportJob
        fields = (
            "id",
            "group_id",
            "airtable_share_id",
            "progress_percentage",
            "state",
            "error",
        )


class CreateAirtableImportJobSerializer(serializers.Serializer):
    group_id = serializers.IntegerField(required=True, help_text="")
    airtable_share_url = serializers.URLField(required=True, help_text="")
