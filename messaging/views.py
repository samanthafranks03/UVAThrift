from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User as DjangoUser
from . import models
from django.db.models import Q
from .models import Messaging, Notification


def chat_list(request: HttpRequest) -> HttpResponse:
    if not request.session.get('user_data'):
        return redirect('/login/')
    
    email = request.session['user_data']['email']
    user = DjangoUser.objects.get_or_create(
        username=email,
        defaults={'email': email}
    )[0]

    search_query = request.GET.get("search", "").strip()

    if search_query:
        # Show all users matching the search (except yourself)
        users = DjangoUser.objects.filter(username__icontains=search_query).exclude(id=user.id)
    else:
        # Show only users you've messaged or received messages from
        messaged_user_ids = models.Messaging.objects.filter(
            Q(author=user) | Q(recipient=user)
        ).values_list("author", "recipient")

        user_ids = set()
        for author_id, recipient_id in messaged_user_ids:
            if author_id != user.id:
                user_ids.add(author_id)
            if recipient_id != user.id:
                user_ids.add(recipient_id)

        users = DjangoUser.objects.filter(id__in=user_ids)

    return render(request, "messaging/chat_list.html", {
        "users": users,
        "search_query": search_query
    })
    


def chat_view(request: HttpRequest, username: str) -> HttpResponse:
    # Check if user is logged in
    if not request.session.get('user_data'):
        return redirect('/login/')
    
    other_user = get_object_or_404(DjangoUser, username=username)
    email = request.session['user_data']['email']
    user = DjangoUser.objects.get_or_create(
        username=email,
        defaults={'email': email}
    )[0]

    messages = models.Messaging.objects.filter(
        Q(author=user, recipient=other_user) | Q(author=other_user, recipient=user)
    ).order_by("created_at")

    return render(request, "messaging/chat.html", {"messages": messages, "other_user": other_user})


def send_message(request, username):
    if not request.session.get('user_data'):
        return redirect('/login/')
    
    email = request.session['user_data']['email']
    user = DjangoUser.objects.get_or_create(username=email, defaults={'email': email})[0]
    recipient = get_object_or_404(DjangoUser, username=username)

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            message = Messaging.objects.create(author=user, recipient=recipient, content=content)
            Notification.objects.create(recipient=recipient, message=message)

    return redirect("messaging:chat", username=username)

def notifications(request):
    if not request.session.get('user_data'):
        return redirect('/login/')
    
    email = request.session['user_data']['email']
    user = DjangoUser.objects.get(username=email)

    unread = models.Notification.objects.filter(recipient=user, is_read=False).order_by("-created_at")
    return render(request, "messaging/notifications.html", {"notifications": unread})

@require_http_methods(["POST"])
def mark_read(request, notification_id):
    if not request.session.get('user_data'):
        return redirect('/login/')
    
    email = request.session['user_data']['email']
    user = DjangoUser.objects.get(username=email)

    note = get_object_or_404(models.Notification, id=notification_id, recipient=user)
    note.is_read = True
    note.save()
    return redirect("messaging:notifications")