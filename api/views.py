import json

from django.http.response import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .drop_classify_utils import drop_classify


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def drop_classify_view(request):
    return JsonResponse(drop_classify(json.loads(request.body)))