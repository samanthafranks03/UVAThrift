from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from . import models
from django.db.models import Q


@login_required
def chat_list(request: HttpRequest) -> HttpResponse:
    """
    Shows all unique users you've chatted with (sent or received).
    """
    user = request.user
    sent_to = models.Messaging.objects.filter(author=user).values_list("recipient", flat=True)
    received_from = models.Messaging.objects.filter(recipient=user).values_list("author", flat=True)

    user_ids = set(list(sent_to) + list(received_from))
    users = User.objects.filter(id__in=user_ids).exclude(id=user.id)

    return render(request, "messaging/chat_list.html", {"users": users})


@login_required
def chat_view(request: HttpRequest, username: str) -> HttpResponse:
    """
    Displays the conversation between the current user and another user.
    """
    other_user = get_object_or_404(User, username=username)
    user = request.user

    # Only show messages between these two users
    messages = models.Messaging.objects.filter(
        Q(author=user, recipient=other_user) | Q(author=other_user, recipient=user)
    ).order_by("created_at")

    return render(request, "messaging/chat.html", {"messages": messages, "other_user": other_user})


@login_required
@require_http_methods(["POST"])
def send_message(request: HttpRequest, username: str) -> HttpResponse:
    """
    Send a message to another user.
    """
    other_user = get_object_or_404(User, username=username)
    content = request.POST.get("content", "").strip()
    if not content:
        return redirect("messaging:chat", username=other_user.username)

    models.Messaging.objects.create(author=request.user, recipient=other_user, content=content)
    return redirect("messaging:chat", username=other_user.username)
