class DatabaseExportSerializedStructure:
    @staticmethod
    def database(tables):
        return {"tables": tables}

    @staticmethod
    def table(id, name, order, fields, views, rows):
        return {
            "id": id,
            "name": name,
            "order": order,
            "fields": fields,
            "views": views,
            "rows": rows,
        }

    @staticmethod
    def row(id, order):
        return {
            "id": id,
            "order": order,
        }

    @staticmethod
    def file_field_value(name, visible_name, original_name):
        return {
            "name": name,
            "visible_name": visible_name,
            "original_name": original_name,
        }
