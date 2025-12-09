# REFERENCES
# Claude 4.5
# Use: Implementing S3 presigned URL generation for post image uploads

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count
from django.conf import settings
import boto3
import uuid
import logging

from users.models import User
from .models import Post, PostFlag, Bookmark
from messaging.models import Messaging, Notification
from django.contrib.auth.models import User as DjangoUser

@require_http_methods(["GET"])
def feed(request):
    """Show all posts (home feed)."""
    posts = Post.objects.select_related("author").filter(status="active")

    # Add flag information for each post if user is logged in
    user_data = request.session.get("user_data", {})
    email = user_data.get("email")
    current_user = None

    if email:
        try:
            current_user = User.objects.get(email=email)
            bookmarked_ids = set(
                Bookmark.objects.filter(user=current_user, post__in=posts).values_list("post_id", flat=True)
            )
            for post in posts:
                post.is_flagged_by_current_user = post.is_flagged_by_user(current_user)
                post.is_bookmarked_by_current_user = post.id in bookmarked_ids
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

    # Get post text
    title = request.POST.get("title", "").strip() or "Unnamed Item"
    location = request.POST.get("location", "").strip() or "Location not provided"
    content = request.POST.get("content", "").strip()

    # Prefer image_key (S3 key) if client uploaded directly to S3; fall back to file upload
    image_key = request.POST.get('image_key')
    image_file = request.FILES.get('image')

    if not image_key and not image_file:
        messages.error(request, "Please attach an image to your post.")
        return redirect("/market/")

    if not content:
        messages.error(request, "Post cannot be empty.")
        return redirect("/market/")

    # Create post. If we got an image_key, store it into the ImageField name so
    # storage.url() or a presigned GET redirect can serve it; otherwise save uploaded file.
    if image_key:
        post = Post(author=user, title=title, content=content, location=location)
        post.image.name = image_key
        post.save()
    else:
        Post.objects.create(
            author=user,
            title=title,
            content=content,
            location=location,
            image=image_file,
        )
        post = Post.objects.create(author=user, content=content, image=image_file)

    tags_str = request.POST.get("tags", "")
    if tags_str:
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        post.tags.set(tags)

    messages.success(request, "Post created successfully!")
    return redirect("/market/")


@require_http_methods(["GET"])
def s3_presign(request, hashed_email):
    """Return a presigned PUT URL and a key for uploading a post image.

    Query params: filename and content_type (optional).
    Only the session owner may request a presign for their own posts.
    """
    session_user = request.session.get('user_data', {})
    if not session_user or session_user.get('email') is None:
        return JsonResponse({'error': 'not-signed-in'}, status=403)
    try:
        user = User.objects.get(hashed_email=hashed_email)
    except User.DoesNotExist:
        return JsonResponse({'error': 'user-not-found'}, status=404)
    if session_user.get('email') != user.email:
        return JsonResponse({'error': 'not-owner'}, status=403)

    filename = request.GET.get('filename')
    content_type = request.GET.get('content_type') or 'application/octet-stream'
    if not filename:
        return JsonResponse({'error': 'missing filename'}, status=400)

    ext = ''
    if '.' in filename:
        ext = filename[filename.rfind('.'):]
    key = f"post_images/{user.hashed_email}_{uuid.uuid4().hex}{ext}"

    bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    if not bucket:
        logging.getLogger(__name__).warning('posts.s3_presign called but AWS_STORAGE_BUCKET_NAME not configured')
        return JsonResponse({'error': 'S3 bucket not configured'}, status=400)

    s3 = boto3.client('s3')
    params = {'Bucket': bucket, 'Key': key, 'ContentType': content_type}
    try:
        url = s3.generate_presigned_url('put_object', Params=params, ExpiresIn=3600)
    except Exception as e:
        logging.getLogger(__name__).exception('presign generation failed')
        return JsonResponse({'error': f'presign-failed: {e}'}, status=400)

    return JsonResponse({'url': url, 'key': key})


@require_http_methods(["POST"])
def set_post_image(request, hashed_email):
    """Simple endpoint that accepts JSON/form with 'key' and validates ownership.

    The client calls this after uploading to S3; we echo back the key so the client
    can include it in the create_post form.
    """
    session_user = request.session.get('user_data', {})
    if not session_user or session_user.get('email') is None:
        return JsonResponse({'error': 'not-signed-in'}, status=403)
    try:
        user = User.objects.get(hashed_email=hashed_email)
    except User.DoesNotExist:
        return JsonResponse({'error': 'user-not-found'}, status=404)
    if session_user.get('email') != user.email:
        return JsonResponse({'error': 'not-owner'}, status=403)

    key = request.POST.get('key') or None
    if not key:
        try:
            import json
            payload = json.loads(request.body.decode() or '{}')
            key = payload.get('key')
        except Exception:
            key = None

    if not key:
        return JsonResponse({'error': 'missing key'}, status=400)

    return JsonResponse({'ok': True, 'key': key})


@require_http_methods(["GET"])
def post_image(request, post_id):
    """Redirect to a presigned GET URL for the post image (if stored in S3).

    This allows templates to reference `{% url 'post-image' post.id %}` for images
    whether they are stored locally or as S3 keys saved in the ImageField.name.
    """
    post = get_object_or_404(Post, id=post_id)
    key = getattr(post.image, 'name', None)
    if not key:
        return HttpResponse(status=404)

    bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    if not bucket:
        # If no S3 configured, try the storage backend URL (may work if using local MEDIA)
        try:
            url = post.image.url
            return HttpResponseRedirect(url)
        except Exception:
            return HttpResponse(status=404)

    s3 = boto3.client('s3')
    try:
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
    except Exception:
        logging.getLogger(__name__).exception('failed to generate presigned GET for post image')
        return HttpResponse(status=500)

    return HttpResponseRedirect(url)


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


@require_http_methods(["POST"])
def toggle_post_status(request, post_id):
    """Allow the author to close/reopen their post."""
    user_data = request.session.get("user_data", {})
    email = user_data.get("email")
    if not email:
        messages.error(request, "Please sign in to update listings.")
        return redirect("/login/")

    post = get_object_or_404(Post, id=post_id)
    if post.author.email != email:
        return HttpResponse("Forbidden", status=403)

    previous_status = post.status
    post.status = "closed" if post.status == "active" else "active"
    post.save(update_fields=["status"])

    # Notify bookmarked users when a listing is closed
    if previous_status == "active" and post.status == "closed":
        actor = post.author
        actor_dj, _ = DjangoUser.objects.get_or_create(
            username=actor.email,
            defaults={"email": actor.email},
        )
        bookmarked = Bookmark.objects.filter(post=post).select_related("user")
        for bm in bookmarked:
            recipient_profile = bm.user
            if recipient_profile.email == actor.email:
                continue
            recipient_dj, _ = DjangoUser.objects.get_or_create(
                username=recipient_profile.email,
                defaults={"email": recipient_profile.email},
            )
            note_text = f"{actor.nickname or actor.name or 'Someone'} closed the post \"{post.title or 'your post'}\" you bookmarked."
            msg = Messaging.objects.create(author=actor_dj, recipient=recipient_dj, content=note_text)
            Notification.objects.create(recipient=recipient_dj, message=msg)
    # Notify author/bookmarkers when reopened
    elif previous_status == "closed" and post.status == "active":
        actor = post.author
        actor_dj, _ = DjangoUser.objects.get_or_create(
            username=actor.email,
            defaults={"email": actor.email},
        )
        bookmarked = Bookmark.objects.filter(post=post).select_related("user")
        for bm in bookmarked:
            recipient_profile = bm.user
            if recipient_profile.email == actor.email:
                continue
            recipient_dj, _ = DjangoUser.objects.get_or_create(
                username=recipient_profile.email,
                defaults={"email": recipient_profile.email},
            )
            note_text = f"{actor.nickname or actor.name or 'Someone'} reopened the post \"{post.title or 'your post'}\"."
            msg = Messaging.objects.create(author=actor_dj, recipient=recipient_dj, content=note_text)
            Notification.objects.create(recipient=recipient_dj, message=msg)

    next_url = request.POST.get("next") or post.author.get_absolute_url()
    status_label = "closed" if post.status == "closed" else "reopened"
    messages.success(request, f"Listing {status_label}.")
    return redirect(next_url)

def toggle_bookmark(request, post_id):
    """Toggle bookmark status for a post"""
    user_data = request.session.get("user_data", {})
    email = user_data.get("email")

    if not email:
        return JsonResponse({"error": "Please sign in to bookmark posts."}, status=401)

    try:
        user = User.objects.get(email=email)
        post = get_object_or_404(Post, id=post_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    existing = Bookmark.objects.filter(user=user, post=post).first()
    if existing:
        existing.delete()
        is_bookmarked = False
        message = "Bookmark removed."
    else:
        Bookmark.objects.create(user=user, post=post)
        is_bookmarked = True
        message = "Post bookmarked."

        # Notify the post author (via messaging notification) when someone bookmarks their post
        if post.author.email != user.email:
            recipient_dj, _ = DjangoUser.objects.get_or_create(
                username=post.author.email,
                defaults={"email": post.author.email},
            )
            sender_dj, _ = DjangoUser.objects.get_or_create(
                username=user.email,
                defaults={"email": user.email},
            )
            note_text = f"{user.nickname or user.name or 'Someone'} bookmarked your post \"{post.title or 'your post'}\"."
            msg = Messaging.objects.create(author=sender_dj, recipient=recipient_dj, content=note_text)
            Notification.objects.create(recipient=recipient_dj, message=msg)

    return JsonResponse({
        "success": True,
        "is_bookmarked": is_bookmarked,
        "message": message,
    })


@require_http_methods(["GET"])
def bookmarks_list(request):
    """Show all bookmarks for the signed-in user."""
    user_data = request.session.get("user_data", {})
    email = user_data.get("email")

    if not email:
        return redirect("/login/")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return redirect("/login/")

    bookmarks = (
        Bookmark.objects.filter(user=user, post__status="active")
        .select_related("post__author")
        .order_by("-created_at")
    )

    posts = [b.post for b in bookmarks]
    for post in posts:
        post.is_bookmarked_by_current_user = True
        post.is_flagged_by_current_user = post.is_flagged_by_user(user)

    context = {
        "bookmarks": bookmarks,
        "posts": posts,
        "current_user": user,
    }
    return render(request, "posts/bookmarks.html", context)


########## Admin Views ##########

@csrf_protect
@require_http_methods(["GET"])
def admin_flagged_posts(request):
    """Admin view to see all flagged posts"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        return HttpResponse('Forbidden: Admin access required', status=403)

    # Get all posts with flags, ordered by flag count (most flagged first)
    flagged_posts = Post.objects.annotate(
        flag_count_db=Count('postflag')
    ).filter(flag_count_db__gt=0).select_related('author').order_by('-flag_count_db')

    # Add flag details to each post
    for post in flagged_posts:
        post.flags = PostFlag.objects.filter(post=post).select_related('user')

    context = {
        "flagged_posts": flagged_posts,
        "total_flagged": flagged_posts.count()
    }
    return render(request, "posts/admin_flagged_posts.html", context)


@csrf_protect
@require_http_methods(["POST"])
def admin_delete_post(request, post_id):
    """Admin action to delete a flagged post"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        return HttpResponse('Forbidden: Admin access required', status=403)

    try:
        post = get_object_or_404(Post, id=post_id)
        post_content = post.content[:50] + "..." if len(post.content) > 50 else post.content
        post.delete()
        messages.success(request, f"Post deleted successfully: '{post_content}'")
    except Exception as e:
        messages.error(request, f"Error deleting post: {str(e)}")

    return redirect('admin_flagged_posts')


@csrf_protect
@require_http_methods(["POST"])
def admin_dismiss_flags(request, post_id):
    """Admin action to dismiss all flags for a post without deleting it"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        return HttpResponse('Forbidden: Admin access required', status=403)

    try:
        post = get_object_or_404(Post, id=post_id)
        flag_count = post.flag_count()
        PostFlag.objects.filter(post=post).delete()
        messages.success(request, f"Dismissed {flag_count} flag(s) for post.")
    except Exception as e:
        messages.error(request, f"Error dismissing flags: {str(e)}")

    return redirect('admin_flagged_posts')


@csrf_protect
@require_http_methods(["POST"])
def admin_ban_and_delete(request, post_id):
    """Admin action to ban the user and delete their flagged post"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        return HttpResponse('Forbidden: Admin access required', status=403)

    try:
        post = get_object_or_404(Post, id=post_id)
        user = post.author
        post_content = post.content[:50] + "..." if len(post.content) > 50 else post.content

        # Ban the user
        user.is_flagged = True
        user.save()

        # Delete the post
        post.delete()

        messages.success(request, f"User '{user.name}' has been banned and their post deleted: '{post_content}'")
    except Exception as e:
        messages.error(request, f"Error banning user and deleting post: {str(e)}")

    return redirect('admin_flagged_posts')


@csrf_protect
@require_http_methods(["GET"])
def admin_flagged_posts_api(request):
    """API endpoint to get flagged posts data as JSON"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        return JsonResponse({"error": "Forbidden: Admin access required"}, status=403)

    # Get all posts with flags, ordered by flag count (most flagged first)
    flagged_posts = Post.objects.annotate(
        flag_count_db=Count('postflag')
    ).filter(flag_count_db__gt=0).select_related('author').order_by('-flag_count_db')

    # Prepare data for JSON response
    posts_data = []
    for post in flagged_posts:
        flags_data = []
        for flag in PostFlag.objects.filter(post=post).select_related('user'):
            flags_data.append({
                'user_name': flag.user.name,
                'user_email': flag.user.email,
                'created_at': flag.created_at.strftime('%b %d')
            })

        posts_data.append({
            'id': post.id,
            'content': post.content,
            'author_name': post.author.name,
            'author_email': post.author.email,
            'created_at': post.created_at.strftime('%b %d, %Y %H:%M'),
            'flag_count': post.flag_count_db,
            'flags': flags_data
        })

    return JsonResponse({
        'flagged_posts': posts_data,
        'total_flagged': len(posts_data)
    })
