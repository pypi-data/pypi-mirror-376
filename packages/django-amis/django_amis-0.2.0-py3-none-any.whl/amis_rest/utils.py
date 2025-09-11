import pandas as pd
from io import BytesIO
from django.http import HttpResponse

def queryset_to_excel(queryset, fields, filename="export.xlsx"):
    df = pd.DataFrame(list(queryset.values(*fields)))
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    response = HttpResponse(
        output,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response

def queryset_to_csv(queryset, fields, filename="export.csv"):
    df = pd.DataFrame(list(queryset.values(*fields)))
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    response = HttpResponse(output, content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
