from django.shortcuts import render, redirect
from users.models import User
from posts.models import Post


def home(request):
    """
    Market page:
    - Checks if a Google-authenticated session exists.
    - Ensures the user exists in the database.
    - Redirects banned users to their profile.
    - Shows post form if signed in and not banned.
    """
    user_data = request.session.get("user_data")
    user = None
    can_post = False

    if user_data:
        email = user_data.get("email")
        name = user_data.get("given_name", "Anonymous")
        picture = user_data.get("picture", "")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "name": name,
                "picture_url": picture,
                "is_new_user": True,
            },
        )

        if user.is_flagged:
            user_url = request.session.get("user_URL") or user.get_absolute_url()
            request.session["user_URL"] = user_url
            return redirect(user_url)

        can_post = True

    #Grabs all the posts from our db
    posts = Post.objects.select_related("author").all()
    
    # Add flag information for each post if user is logged in
    if user:
        for post in posts:
            post.is_flagged_by_current_user = post.is_flagged_by_user(user)

    # Check if user should see walkthrough
    show_walkthrough = False
    if user and not user.has_seen_walkthrough:
        show_walkthrough = True

    context = {
        "posts": posts,
        "user": user,
        "current_user": user,  # Add current_user to context for template
        "can_post": can_post,
        "show_walkthrough": show_walkthrough,
    }
    return render(request, "home_page.html", context)
