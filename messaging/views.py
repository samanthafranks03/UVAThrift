from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User as DjangoUser
from . import models
from django.db.models import Q
from .models import Messaging, Notification, Group, GroupMessage
from users.models import User as ProfileUser

def get_display_name(django_user):
    # Get the name for a Django user, fallback to email
    try:
        profile_user = ProfileUser.objects.get(email=django_user.username)
        return profile_user.name if profile_user.name else django_user.username
    except ProfileUser.DoesNotExist:
        return django_user.username

def chat_list(request: HttpRequest) -> HttpResponse:
    if not request.session.get('user_data'):
        return redirect('/login/')
    
    email = request.session['user_data']['email']
    user = DjangoUser.objects.get_or_create(
        username=email,
        defaults={'email': email}
    )[0]

    search_query = request.GET.get("search", "").strip()

    # Individual chats
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
    if search_query:
        users = users.filter(username__icontains=search_query)

    # Add display name for each user
    for u in users:
        u.display_name = get_display_name(u)

    # Group chats
    groups = models.Group.objects.filter(members=user)
    if search_query:
        groups = groups.filter(name__icontains=search_query)

    return render(request, "messaging/chat_list.html", {
        "users": users,
        "groups": groups,
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

    other_user.display_name = get_display_name(other_user)

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

    
def group_chat_view(request: HttpRequest, group_id: int) -> HttpResponse:
    if not request.session.get('user_data'):
        return redirect('/login/')
    
    email = request.session['user_data']['email']
    user = DjangoUser.objects.get(username=email)
    group = get_object_or_404(models.Group, id=group_id)

    if user not in group.members.all():
        return redirect("messaging:chat-list")

    messages = models.GroupMessage.objects.filter(group=group).order_by("timestamp")

    return render(request, "messaging/group_chat.html", {
        "group": group,
        "messages": messages
    })

@require_http_methods(["POST"])
def send_group_message(request: HttpRequest, group_id: int) -> HttpResponse:
    if not request.session.get('user_data'):
        return redirect('/login/')
    
    email = request.session['user_data']['email']
    user = DjangoUser.objects.get(username=email)
    group = get_object_or_404(models.Group, id=group_id)

    if user not in group.members.all():
        return redirect("messaging:chat-list")

    content = request.POST.get("content", "").strip()
    if content:
        models.GroupMessage.objects.create(group=group, author=user, content=content)

    return redirect("messaging:group-chat", group_id=group.id)

def start_chat(request: HttpRequest) -> HttpResponse:
    if not request.session.get('user_data'):
        return redirect('/login/')

    email = request.session['user_data']['email']
    user = DjangoUser.objects.get_or_create(username=email, defaults={'email': email})[0]

    search_query = request.GET.get("search", "").strip()

    
    # Sync ProfileUsers to DjangoUsers - makes sure all users from the posts app are available in the messaging system
    profile_users = ProfileUser.objects.all()
    for profile_user in profile_users:
        DjangoUser.objects.get_or_create(
            username=profile_user.email,
            defaults={'email': profile_user.email}
        )
    
    # Get all DjangoUsers except the current user
    users = DjangoUser.objects.exclude(id=user.id)
    if search_query:
        users = users.filter(username__icontains=search_query)

    # Add display_name to each user
    for u in users:
        u.display_name = get_display_name(u)

    if request.method == "POST":
        selected_ids = request.POST.getlist("members")
        if selected_ids:
            if len(selected_ids) == 1:
                selected_user = DjangoUser.objects.get(id=selected_ids[0])
                return redirect("messaging:chat", username=selected_user.username)
            else:
                selected_users = DjangoUser.objects.filter(id__in=selected_ids)
                group_name = "Group with " + ", ".join([user.username] + [u.username for u in selected_users])
                group = models.Group.objects.create(name=group_name)
                group.members.add(user, *selected_users)
                return redirect("messaging:group-chat", group_id=group.id)

    return render(request, "messaging/start_chat.html", {
        "users": users,
        "search_query": search_query
    })
