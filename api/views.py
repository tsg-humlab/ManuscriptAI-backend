import json

from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from api.paths.drop_classify import drop_classify
from api.paths.property_structuring import send_manuscipts
from api.paths.rdfData import transform_data_into_rdf
from api.models import Activity
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from django.contrib.auth import authenticate, login, logout
from .forms import CreateUserForm
# ============ issue #1, EK =====
from datetime import datetime
# ===============================


@ensure_csrf_cookie
@require_http_methods(['GET'])
def set_csrf_token(request):
    """
    We set the CSRF cookie on the frontend.
    """
    return JsonResponse({'message': 'CSRF cookie set'})

@require_http_methods(['POST'])
def login_view(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = data['username']
        password = data['password']
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'message': 'Invalid JSON'}, status=400
        )

    user = authenticate(request, username=username, password=password)

    if user:
        login(request, user)
        return JsonResponse({'success': True})
    return JsonResponse(
        {'success': False, 'message': 'Invalid credentials'}, status=401
    )

def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out'})

@require_http_methods(['GET'])
def user(request):
    if request.user.is_authenticated:
        return JsonResponse(
            {'username': request.user.username, 'email': request.user.email}
        )
    return JsonResponse(
        {'message': 'Not logged in'}, status=401
    )

@require_http_methods(['POST'])
def register(request):
    data = json.loads(request.body.decode('utf-8'))
    form = CreateUserForm(data)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': 'User registered successfully'}, status=201)
    else:
        errors = form.errors.as_json()
        return JsonResponse({'error': errors}, status=400)

@require_http_methods(["POST"])
@login_required
def drop_classify_view(request):
    """
    Example JSON output:
    { "structured_data": [
        { "manuscript_ID": "Tsg Humanities 8",
          "century_of_creation": "12th",
          "support_type": "parchment" },
        { "manuscript_ID": "Tsg Humanities 9",
          "century_of_creation": "13th",
          "support_type": "leather"   },
      ]
    }
    """    
    input = json.loads(request.body)
    output = drop_classify(input)
    # ===== issue #1, EK ============
    obj = Activity.objects.create(user=request.user, endpoint='drop_classify', input=input, output=output)
    # Determine the signature
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    oSignature = dict(method="drop_classify", activity_id=obj.id, time=timestamp)
    if output and "structured_data" in output:
        # Inject the signature into each Manuscript item
        for oItem in output.get("structured_data"):
            oItem['signature'] = oSignature
        # Now save the Activity again, with the updated `output`
        obj.output = output
        obj.save()
    # ===============================
    return JsonResponse(output)

@require_http_methods(["POST"])
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
@login_required
def send_manuscripts_view(request):
    """
    Example JSON output:
    { "structured_results": [
        { "Manuscript 1": "[{\"manuscript_ID\": \"SomeId\", \"field2\": \"some value\"}]"},
        { "Manuscript 2": "[..(stringified JSON list with 1 object)..]"},
        { "Manuscript 3": "[..(stringified JSON list with 1 object)..]"},
      ]
    }
    """
    input = json.loads(request.body)
    output, status = send_manuscipts(input)
    # ===== issue #1, EK ============
    # First record this activity, so as to get the `activity_id`
    obj = Activity.objects.create(user=request.user, endpoint='send_manuscripts', input=input, output=output)
    # Determine the signature
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    oSignature = dict(method="send_manuscripts", activity_id=obj.id, time=timestamp)
    # Walk the structured results list in the output
    if output and "structured_results" in output:
        # Review each manuscript result
        for idx, oOneResult in enumerate(output.get("structured_results")):
            key = "Manuscript {}".format(idx+1)
            sManu = oOneResult[key]
            if sManu:
                # Transform into object
                oManu = json.loads(sManu)
                # Inject signature into this manuscript item
                if len(oManu) > 0 and "signature" in oManu[0]:
                    oManu[0]['signature'] = oSignature
                    # Place back
                    oOneResult[key] = json.dumps(oManu)
        # Now save the Activity again, with the updated `output`
        obj.output = output
        obj.save()
    # ===============================
    return JsonResponse(output, status=status)


@require_http_methods(["POST"])
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
    input = json.loads(request.body)
    print("manuscripts_data:", input)
    output = transform_data_into_rdf(input)
    print("rdf_output:", output)
    # ===== issue #1, EK ============
    if input and isinstance(input, list):
        # We are expecting a list of JSON objects, where each object just has the field "data"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        oSignature = dict(method="manual", activity_id=None, time=timestamp)
        for oItem in input:
            data = oItem.get("data")
            if data:
                # Check: do we already have a signature?
                sig = data.get("signature")
                if sig is None:
                    data['signature'] = oSignature
    # ===============================
    Activity.objects.create(user=request.user, endpoint='transform', input=input, output=output)
    return HttpResponse(output, content_type="text/turtle")
