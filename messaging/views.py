from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User as DjangoUser
from . import models
from django.db.models import Q


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


@require_http_methods(["POST"])
def send_message(request: HttpRequest, username: str) -> HttpResponse:
    # Check if user is logged in
    if not request.session.get('user_data'):
        return redirect('/login/')
    
    other_user = get_object_or_404(DjangoUser, username=username)
    email = request.session['user_data']['email']
    user = DjangoUser.objects.get_or_create(
        username=email,
        defaults={'email': email}
    )[0]
    
    content = request.POST.get("content", "").strip()
    if not content:
        return redirect("messaging:chat", username=other_user.username)

    models.Messaging.objects.create(author=user, recipient=other_user, content=content)
    return redirect("messaging:chat", username=other_user.username)

def group_list(request):
    user = get_current_user(request)
    groups = Group.objects.filter(members=user)
    return render(request, "messaging/group_list.html", {"groups": groups})

def group_chat(request, group_id):
    user = get_current_user(request)
    group = get_object_or_404(Group, id=group_id, members=user)
    messages = GroupMessage.objects.filter(group=group).order_by("created_at")
    return render(request, "messaging/group_chat.html", {"group": group, "messages": messages})

@require_http_methods(["POST"])
def send_group_message(request, group_id):
    user = get_current_user(request)
    group = get_object_or_404(Group, id=group_id, members=user)
    content = request.POST.get("content", "").strip()
    if content:
        GroupMessage.objects.create(group=group, author=user, content=content)
    return redirect("messaging:group-chat", group_id=group.id)