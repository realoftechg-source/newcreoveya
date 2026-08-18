from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from notifications.models import Notification


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'notifications/notifications.html', {'notifications': notifications})


@login_required
@require_POST
def mark_all_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('notifications:home')


@login_required
@require_POST
def mark_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('notifications:home')


@login_required
@require_POST
def delete_notification_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('notifications:home')
