from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from studio.models import Stream


@login_required
def home_view(request):
    user = request.user
    today = timezone.now().date()
    month_start = today.replace(day=1)

    # "idle" rows are just preview/draft sessions created when the studio
    # page loads — they shouldn't count as a stream until the user actually
    # goes live (started_at gets set).
    went_live = Stream.objects.filter(user=user, started_at__isnull=False)

    today_streams = went_live.filter(started_at__date=today).count()
    month_streams = went_live.filter(started_at__date__gte=month_start).count()
    active_stream = Stream.objects.filter(user=user, status='live').first()
    recent_streams = went_live.order_by('-created_at')[:5]

    total_credits_used = sum(s.credits_used for s in went_live)

    context = {
        'today_streams': today_streams,
        'month_streams': month_streams,
        'active_stream': active_stream,
        'recent_streams': recent_streams,
        'total_credits_used': total_credits_used,
        'bandwidth_used_gb': round(month_streams * 0.35, 2),   # placeholder estimate
        'storage_used_gb': round(went_live.count() * 0.12, 2),  # placeholder estimate
        'api_status': 'Active' if settings.AI_ENGINE_CONNECTED else 'Awaiting Integration',
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def settings_view(request):
    return render(request, 'settings/settings.html')


@login_required
def tutorial_view(request):
    return render(request, 'tutorial/tutorial.html')


@login_required
def feed_view(request):
    streams = Stream.objects.filter(status__in=['live', 'ended']).select_related('user').order_by('-created_at')[:30]
    return render(request, 'dashboard/feed.html', {'streams': streams})


@login_required
def ai_jobs_view(request):
    jobs = Stream.objects.filter(user=request.user, started_at__isnull=False).order_by('-created_at')[:50]
    return render(request, 'dashboard/ai_jobs.html', {'jobs': jobs})
