from django.shortcuts import render, redirect
from django.http import HttpRequest, StreamingHttpResponse, HttpResponse
from datetime import datetime
from typing import AsyncGenerator
import asyncio
import json

from . import models


def chat(request: HttpRequest) -> HttpResponse:
    # Ensure only logged-in users can access chat
    if not request.user.is_authenticated:
        return redirect('sign_in')
    return render(request, 'chat.html', {'username': request.user.username})

# def inbox(request):
#     # Get all messages belonging to this user (example logic)
#     messages = models.Messaging.objects.filter(author=request.user).order_by('-created_at')
#     return render(request, 'messaging/inbox.html', {'messages': messages})
def inbox(request):
    user_data = request.session.get("user_data")
    if not user_data:
        return redirect("/login/")

    # Use email, since that's how you store users
    user_email = user_data["email"]

    messages = models.Messaging.objects.filter(
        author__email=user_email
    ).order_by("-created_at")

    return render(request, "messaging/inbox.html", {"messages": messages})



def create_message(request: HttpRequest) -> HttpResponse:
    # Ensure authenticated user
    if not request.user.is_authenticated:
        return HttpResponse(status=403)

    content = request.POST.get("content")

    if content:
        # Directly use the logged-in user
        models.Messaging.objects.create(author=request.user, content=content)
        return HttpResponse(status=201)
    else:
        return HttpResponse(status=200)


async def stream_chat_messages(request: HttpRequest) -> StreamingHttpResponse:
    """
    Streams chat messages to the client as they are created.
    """

    async def event_stream():
        # First send all existing messages
        async for message in get_existing_messages():
            yield message

        last_id = await get_last_message_id()

        # Then continuously check for new ones
        while True:
            new_messages = models.Messaging.objects.filter(id__gt=last_id).order_by('created_at').values(
                'id', 'author__username', 'content'
            )
            async for message in new_messages:
                yield f"data: {json.dumps(message)}\n\n"
                last_id = message['id']
            await asyncio.sleep(0.1)

    async def get_existing_messages() -> AsyncGenerator:
        messages = models.Messaging.objects.all().order_by('created_at').values(
            'id', 'author__username', 'content'
        )
        async for message in messages:
            yield f"data: {json.dumps(message)}\n\n"

    async def get_last_message_id() -> int:
        last_message = await models.Messaging.objects.all().alast()
        return last_message.id if last_message else 0

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
