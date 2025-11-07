from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import JsonResponse
from users.models import User
from .models import Post, PostFlag

@require_http_methods(["GET"])
def feed(request):
    """Show all posts (home feed)."""
    posts = Post.objects.select_related("author").all()
    
    # Add flag information for each post if user is logged in
    user_data = request.session.get("user_data", {})
    email = user_data.get("email")
    current_user = None
    
    if email:
        try:
            current_user = User.objects.get(email=email)
            for post in posts:
                post.is_flagged_by_current_user = post.is_flagged_by_user(current_user)
        except User.DoesNotExist:
            pass
    
    context = {
        "posts": posts,
        "current_user": current_user
    }
    return render(request, "posts/post_list.html", context)


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


@require_http_methods(["POST"])
def toggle_flag(request, post_id):
    """Toggle flag status for a post"""
    user_data = request.session.get("user_data", {})
    email = user_data.get("email")
    
    # Check if user is logged in
    if not email:
        return JsonResponse({"error": "Please sign in to flag posts."}, status=401)
    
    try:
        user = User.objects.get(email=email)
        post = get_object_or_404(Post, id=post_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)
    
    # Check if user is trying to flag their own post
    if post.author == user:
        return JsonResponse({"error": "You cannot flag your own posts."}, status=403)
    
    # Check if user has already flagged this post
    existing_flag = PostFlag.objects.filter(user=user, post=post).first()
    
    if existing_flag:
        # Unflag the post
        existing_flag.delete()
        is_flagged = False
        message = "Post unflagged."
    else:
        # Flag the post
        PostFlag.objects.create(user=user, post=post)
        is_flagged = True
        message = "Post flagged."
    
    return JsonResponse({
        "success": True,
        "is_flagged": is_flagged,
        "flag_count": post.flag_count(),
        "message": message
    })
