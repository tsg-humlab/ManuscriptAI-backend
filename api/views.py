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
    input = json.loads(request.body)
    output = drop_classify(input)
    Activity.objects.create(user=request.user, endpoint='drop_classify', input=input, output=output)
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
    input = json.loads(request.body)
    output, status = send_manuscipts(input)
    Activity.objects.create(user=request.user, endpoint='send_manuscripts', input=input, output=output)
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
    Activity.objects.create(user=request.user, endpoint='transform', input=input, output=output)
    return HttpResponse(output, content_type="text/turtle")