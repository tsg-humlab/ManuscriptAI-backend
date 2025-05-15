import json

from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from api.paths.drop_classify import drop_classify
from api.paths.property_structuring import send_manuscipts
from api.paths.rdfData import transform_data_into_rdf


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def drop_classify_view(request):
    input = json.loads(request.body)
    output = drop_classify(input)
    return JsonResponse(output)

@require_http_methods(["POST"])
@csrf_exempt
@login_required
def process_view(request):
    """
    Reads the entire file as raw text and displays
    it on a new page (results.html) with manuscript boxes.
    """
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file part in the request'})

    file = request.FILES['file']
    if file.filename == '':
        return JsonResponse({'error': 'No selected file'})

    try:
        # Read everything as raw text (no chunking here)
        raw_text = file.read().decode('utf-8', errors='replace')

        # Pass raw_text into template to display it
        return render(raw_text, 'results1.html')

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'error': str(e)})


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def send_manuscripts_view(request):
    input = json.loads(request.body)
    output, status = send_manuscipts(input)
    return JsonResponse(output, status=status)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def transform_view(request):
    """
    Example JSON input:
    [
      {
        "data": {
          "manuscript_ID": "ms_001",
          "support_type": "seta antichissima",
          "century_of_creation": "12th century",
          ...
        }
      }
    ]
    """
    manuscripts_data = json.loads(request.body)
    print("manuscripts_data:", manuscripts_data)
    rdf_output = transform_data_into_rdf(manuscripts_data)
    print("rdf_output:", rdf_output)
    return HttpResponse(rdf_output, content_type="text/turtle")