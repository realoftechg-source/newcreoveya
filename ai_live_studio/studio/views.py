from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from api.avatar import AVAILABLE_BACKGROUNDS
from api.stream import is_ai_engine_connected
from studio.forms import LookUploadForm
from studio.models import Look, Stream


def _get_or_create_current_stream(user):
    """The user's idle (previewing) or live stream — created on first visit
    to the studio so a shareable link exists even before going live."""
    stream = Stream.objects.filter(user=user, status__in=['idle', 'live']).order_by('-created_at').first()
    if stream:
        return stream
    return Stream.objects.create(user=user, status='idle')


@login_required
def studio_view(request):
    stream = _get_or_create_current_stream(request.user)
    context = {
        'stream': stream,
        'looks': Look.objects.filter(user=request.user),
        'backgrounds': AVAILABLE_BACKGROUNDS,
        'quality_choices': Stream.QUALITY_CHOICES,
        'resolution_choices': Stream.RESOLUTION_CHOICES,
        'ai_engine_connected': is_ai_engine_connected(),
        'upload_form': LookUploadForm(),
    }
    return render(request, 'studio/studio.html', context)


@login_required
@require_POST
def upload_look_view(request):
    form = LookUploadForm(request.POST, request.FILES)
    if form.is_valid():
        look = form.save(commit=False)
        look.user = request.user
        look.save()
        messages.success(request, f'"{look.name}" added to your looks.')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
    return redirect('studio:home')


@login_required
@require_POST
def delete_look_view(request, look_id):
    look = get_object_or_404(Look, pk=look_id, user=request.user)
    look.image.delete(save=False)
    look.delete()
    messages.success(request, 'Look deleted.')
    return redirect('studio:home')


@login_required
def look_image_view(request, look_id):
    """
    Serves an uploaded look's photo — never through a raw public /media/
    URL. Only the owning user can view their own uploaded faces.
    """
    look = get_object_or_404(Look, pk=look_id)
    if look.user_id != request.user.id:
        raise Http404
    return FileResponse(look.image.open('rb'))


@login_required
def ai_obs_view(request):
    stream = _get_or_create_current_stream(request.user)
    if not request.user.obs_token:
        request.user.generate_obs_token()

    obs_url = request.build_absolute_uri(f'/obs/{request.user.obs_token}/')

    context = {
        'stream': stream,
        'obs_url': obs_url,
        'resolution_choices': Stream.RESOLUTION_CHOICES,
    }
    return render(request, 'studio/ai_obs.html', context)


@login_required
@require_POST
def regenerate_obs_url_view(request):
    request.user.generate_obs_token()
    messages.success(request, 'Your OBS Browser Source URL has been regenerated. Update it in OBS.')
    return redirect('studio:ai_obs')


def watch_view(request, stream_id):
    """
    Public page — anyone with the link can watch, no account required.
    This is the page that was previously 404ing: it now exists and
    connects to the broadcaster in-browser via WebRTC.
    """
    stream = Stream.objects.filter(stream_id=stream_id).select_related('user').first()
    context = {'stream': stream, 'stream_id': stream_id}
    return render(request, 'watch/watch.html', context)


def obs_browser_source_view(request, token):
    """
    Bare, chrome-free page meant to be added as an OBS Browser Source.
    Access is gated by the private token in the URL rather than a login,
    since OBS's embedded browser doesn't carry the user's session.
    """
    from accounts.models import User

    user = User.objects.filter(obs_token=token).first()
    if not user:
        return render(request, 'watch/watch.html', {'stream': None, 'stream_id': None}, status=404)

    stream = Stream.objects.filter(user=user, status__in=['idle', 'live']).order_by('-created_at').first()
    context = {'stream': stream}
    return render(request, 'obs/browser_source.html', context)
