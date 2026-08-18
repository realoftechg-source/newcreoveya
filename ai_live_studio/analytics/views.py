import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from studio.models import Stream


@login_required
def analytics_view(request):
    user = request.user
    today = timezone.now().date()
    last_14_days = [today - timedelta(days=i) for i in range(13, -1, -1)]

    went_live = Stream.objects.filter(user=user, started_at__isnull=False)

    daily_counts = []
    for day in last_14_days:
        count = went_live.filter(started_at__date=day).count()
        daily_counts.append(count)

    watch_time_total = sum(s.duration_seconds for s in went_live.filter(status='ended'))
    credit_usage_total = went_live.aggregate(total=Sum('credits_used'))['total'] or 0
    active_sessions = went_live.filter(status='live').count()

    quality_breakdown = (
        went_live
        .values('quality')
        .annotate(count=Count('id'))
        .order_by('quality')
    )

    context = {
        'labels_json': json.dumps([d.strftime('%b %d') for d in last_14_days]),
        'daily_counts_json': json.dumps(daily_counts),
        'watch_time_total': watch_time_total,
        'credit_usage_total': credit_usage_total,
        'active_sessions': active_sessions,
        'quality_breakdown': list(quality_breakdown),
        'quality_labels_json': json.dumps([q['quality'] for q in quality_breakdown]),
        'quality_counts_json': json.dumps([q['count'] for q in quality_breakdown]),
        'stream_history': went_live.order_by('-created_at')[:20],
    }
    return render(request, 'analytics/analytics.html', context)
