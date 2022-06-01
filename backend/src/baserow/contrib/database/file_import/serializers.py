from rest_framework import serializers


class FailingRowSerializer(serializers.Serializer):
    index = serializers.IntegerField(
        help_text="Index (starts at 0) of the failing row in the original file."
    )
    errors = serializers.DictField(
        child=serializers.ListField(
            child=serializers.CharField(), help_text="Error messages for this field."
        ),
        help_text=(
            "An array of error messages by fields. "
            "The key is the field name and the value is an array of error messages "
            "for this field. These messages are localized for the user "
            "who has created the job."
        ),
    )


class ReportSerializer(serializers.Serializer):
    failing_rows = FailingRowSerializer(
        many=True, help_text="List of failing row reasons."
    )
