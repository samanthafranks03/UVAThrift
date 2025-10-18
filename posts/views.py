from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from users.models import User
from .models import Post

@require_http_methods(["GET"])
def feed(request):
    """Show all posts (home feed)."""
    posts = Post.objects.select_related("author").all()
    return render(request, "posts/post_list.html", {"posts": posts})


@require_http_methods(["POST"])
def create_post(request):
    """Handle form submissions for new posts."""
    user_data = request.session.get("user_data", {})
    email = user_data.get("email")

    #Logged in check
    if not email:
        messages.error(request, "Please sign in to post.")
        return redirect("/login/")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("/login/")

    #Check if the user is banned
    if user.is_flagged:
        messages.error(request, "You are banned and cannot post.")
        return redirect(f"/users/{user.hashed_email}/")

    #Get post text
    content = request.POST.get("content", "").strip()
    if not content:
        messages.error(request, "Post cannot be empty.")
        return redirect("/market/")

    #Save new post
    Post.objects.create(author=user, content=content)
    messages.success(request, "Post created successfully!")
    return redirect("/market/")
