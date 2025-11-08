from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from users.models import User
from .models import Post
from django.conf import settings
from django.http import JsonResponse
import boto3
import uuid
import logging
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse

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

    # Get post text
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
        post = Post(author=user, content=content)
        post.image.name = image_key
        post.save()
    else:
        Post.objects.create(author=user, content=content, image=image_file)
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
