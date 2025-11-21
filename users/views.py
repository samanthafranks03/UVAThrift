from django.shortcuts import render

from django.views.generic import DetailView, UpdateView
from django.urls.base import reverse
from .models import User, UserForm
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
import logging
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.shortcuts import get_object_or_404
import boto3
import uuid
import mimetypes
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.contrib import messages


class UserProfileView(DetailView):
    model = User
    template_name = "profile.html"
    slug_field = "hashed_email"
    slug_url_kwarg = "hashed_email"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all posts by this user, ordered by most recent first
        from posts.models import Post, PostFlag
        from django.db.models import Count
        context['user_posts'] = Post.objects.filter(author=self.object).order_by('-created_at')
        
        # If viewing user is an admin and this is their own profile, add admin panel data
        session_user = self.request.session.get('user_data', {})
        is_admin = self.request.session.get('is_admin', False)
        
        # Check both session is_admin flag AND if viewing own profile
        if is_admin and session_user.get('email') == self.object.email and self.object.is_admin:
            # Get all users for user management
            context['all_users'] = User.objects.all().order_by('name')
            
            # Get flagged posts with flag count
            flagged_posts = Post.objects.annotate(
                flag_count_db=Count('postflag')
            ).filter(flag_count_db__gt=0).select_related('author').order_by('-flag_count_db')
            
            # Add flag details to each post
            for post in flagged_posts:
                post.flags = PostFlag.objects.filter(post=post).select_related('user')
            
            context['flagged_posts'] = flagged_posts
            context['show_admin_panel'] = True
        
        return context


class EditProfileView(UpdateView):
    model = User
    form_class = UserForm
    template_name = "edit_profile.html"
    slug_field = "hashed_email"
    slug_url_kwarg = "hashed_email"

    def get_success_url(self):
        return reverse("user-profile", kwargs={"hashed_email": self.object.hashed_email})


@require_http_methods(["GET"])
def s3_presign(request, hashed_email):
    """Return a presigned PUT URL and the S3 key for the current user.

    Expects query params: filename and content_type (optional). Only the session owner
    may request a presign for their own profile.
    """
    # basic ownership check
    session_user = request.session.get('user_data', {})
    if not session_user or session_user.get('email') is None:
        return JsonResponse({'error': 'not-signed-in'}, status=403)
    user = get_object_or_404(User, hashed_email=hashed_email)
    if session_user.get('email') != user.email:
        return JsonResponse({'error': 'not-owner'}, status=403)

    filename = request.GET.get('filename')
    content_type = request.GET.get('content_type') or 'application/octet-stream'
    if not filename:
        return JsonResponse({'error': 'missing filename'}, status=400)

    # derive extension, build a unique key
    ext = ''
    if '.' in filename:
        ext = filename[filename.rfind('.'):]
    # safe unique name
    key = f"profile_pics/{user.hashed_email}_{uuid.uuid4().hex}{ext}"

    bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    if not bucket:
        logging.getLogger(__name__).warning('s3_presign called but AWS_STORAGE_BUCKET_NAME not configured')
        return JsonResponse({'error': 'S3 bucket not configured'}, status=400)

    # create presigned PUT URL
    s3 = boto3.client('s3')
    params = {
        'Bucket': bucket,
        'Key': key,
        'ContentType': content_type,
    }
    try:
        url = s3.generate_presigned_url('put_object', Params=params, ExpiresIn=3600)
    except Exception as e:
        logging.getLogger(__name__).exception('presign generation failed')
        return JsonResponse({'error': f'presign-failed: {e}'}, status=400)

    return JsonResponse({'url': url, 'key': key})


def s3_serve_picture(request, hashed_email):
    """Return a redirect to a public URL for the user's profile picture.

    If S3 is configured, return a presigned GET URL that allows the browser
    to fetch the object even if the bucket is private. Otherwise, fall back
    to MEDIA_URL + stored key so the local dev server can serve it.
    """
    user = get_object_or_404(User, hashed_email=hashed_email)
    # If no picture set, return 404-ish by redirecting to default or 404 page
    if not user.picture:
        # Redirect to default placeholder in MEDIA
        try:
            default = settings.MEDIA_URL + 'profile_pics/default.jpg'
        except Exception:
            default = '/static/a2_market/default.jpg'
        return HttpResponseRedirect(default)

    key = user.picture.name
    bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    if bucket:
        try:
            s3 = boto3.client('s3')
            url = s3.generate_presigned_url(
                'get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600
            )
            return HttpResponseRedirect(url)
        except Exception:
            logging.getLogger(__name__).exception('failed to generate presigned GET for %s', key)
            # fall through to MEDIA_URL fallback

    # Fallback: serve via MEDIA_URL (works if you use local storage or have set up a proxy)
    try:
        return HttpResponseRedirect(settings.MEDIA_URL + key)
    except Exception:
        return HttpResponseRedirect('/')


@require_http_methods(["POST"])
def set_profile_picture(request, hashed_email):
    """Persist the S3 key returned by the client into the User.picture field.

    Expects POST JSON or form data with 'key'. Checks that the session owner matches.
    """
    session_user = request.session.get('user_data', {})
    if not session_user or session_user.get('email') is None:
        return JsonResponse({'error': 'not-signed-in'}, status=403)
    user = get_object_or_404(User, hashed_email=hashed_email)
    if session_user.get('email') != user.email:
        return JsonResponse({'error': 'not-owner'}, status=403)

    key = request.POST.get('key') or (request.body and None)
    # Try JSON if not in POST
    if not key:
        try:
            import json
            payload = json.loads(request.body.decode() or '{}')
            key = payload.get('key')
        except Exception:
            key = None

    if not key:
        return JsonResponse({'error': 'missing key'}, status=400)

    # Save the key into the ImageField (store the S3 key relative to storage)
    user.picture.name = key
    user.save()

    # Build a public-ish URL if using S3 storage, otherwise rely on storage.url
    try:
        url = user.picture.url
    except Exception:
        # fallback to key
        url = key

    return JsonResponse({'ok': True, 'url': url, 'key': key})


@require_http_methods(["POST"])
def delete_post(request, hashed_email, post_id):
    """Delete a post if the user owns it."""
    session_user = request.session.get('user_data', {})
    if not session_user or session_user.get('email') is None:
        messages.error(request, 'You must be signed in to delete posts.')
        return redirect('/login/')
    
    user = get_object_or_404(User, hashed_email=hashed_email)
    if session_user.get('email') != user.email:
        messages.error(request, 'You can only delete your own posts.')
        return redirect('user-profile', hashed_email=hashed_email)
    
    from posts.models import Post
    post = get_object_or_404(Post, id=post_id, author=user)
    
    # Delete the post
    post.delete()
    messages.success(request, 'Post deleted successfully.')
    
    return redirect('user-profile', hashed_email=hashed_email)


@require_http_methods(["POST"])
def admin_ban_user_profile(request, hashed_email):
    """Admin action to ban a user from profile admin panel"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('user-profile', hashed_email=hashed_email)
    
    target_email = request.POST.get('email')
    try:
        target_user = User.objects.get(email=target_email)
        target_user.is_flagged = True
        target_user.save()
        messages.success(request, f'User {target_user.name} has been banned.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('user-profile', hashed_email=hashed_email)


@require_http_methods(["POST"])
def admin_unban_user_profile(request, hashed_email):
    """Admin action to unban a user from profile admin panel"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('user-profile', hashed_email=hashed_email)
    
    target_email = request.POST.get('email')
    try:
        target_user = User.objects.get(email=target_email)
        target_user.is_flagged = False
        target_user.save()
        messages.success(request, f'User {target_user.name} has been unbanned.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('user-profile', hashed_email=hashed_email)


@require_http_methods(["POST"])
def admin_delete_post_profile(request, hashed_email, post_id):
    """Admin action to delete a flagged post from profile admin panel"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('user-profile', hashed_email=hashed_email)
    
    from posts.models import Post
    try:
        post = get_object_or_404(Post, id=post_id)
        post_content = post.content[:50] + "..." if len(post.content) > 50 else post.content
        post.delete()
        messages.success(request, f'Post deleted successfully: "{post_content}"')
    except Exception as e:
        messages.error(request, f'Error deleting post: {str(e)}')
    
    return redirect('user-profile', hashed_email=hashed_email)


@require_http_methods(["POST"])
def admin_dismiss_flags_profile(request, hashed_email, post_id):
    """Admin action to dismiss all flags for a post from profile admin panel"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('user-profile', hashed_email=hashed_email)
    
    from posts.models import Post, PostFlag
    try:
        post = get_object_or_404(Post, id=post_id)
        flag_count = post.flag_count()
        PostFlag.objects.filter(post=post).delete()
        messages.success(request, f'Dismissed {flag_count} flag(s) for post.')
    except Exception as e:
        messages.error(request, f'Error dismissing flags: {str(e)}')
    
    return redirect('user-profile', hashed_email=hashed_email)


@require_http_methods(["POST"])
def admin_ban_and_delete_profile(request, hashed_email, post_id):
    """Admin action to ban user and delete their post from profile admin panel"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('user-profile', hashed_email=hashed_email)
    
    from posts.models import Post
    try:
        post = get_object_or_404(Post, id=post_id)
        target_user = post.author
        post_content = post.content[:50] + "..." if len(post.content) > 50 else post.content
        
        # Ban the user
        target_user.is_flagged = True
        target_user.save()
        
        # Delete the post
        post.delete()
        
        messages.success(request, f'User "{target_user.name}" has been banned and their post deleted: "{post_content}"')
    except Exception as e:
        messages.error(request, f'Error banning user and deleting post: {str(e)}')
    
    return redirect('user-profile', hashed_email=hashed_email)


########## Admin Control Panel ##########

from django.views.decorators.csrf import csrf_protect

@csrf_protect
def admin_control_panel(request):
    """Admin control panel with tabs for user management and flagged posts"""
    # Check if user is admin
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('/')
    
    from posts.models import Post, PostFlag
    from django.db.models import Count
    
    # Get all users for user management
    all_users = User.objects.all().order_by('name')
    
    # Get flagged posts with flag count
    flagged_posts = Post.objects.annotate(
        flag_count_db=Count('postflag')
    ).filter(flag_count_db__gt=0).select_related('author').order_by('-flag_count_db')
    
    # Add flag details to each post
    for post in flagged_posts:
        post.flags = PostFlag.objects.filter(post=post).select_related('user')
    
    context = {
        'all_users': all_users,
        'flagged_posts': flagged_posts,
    }
    
    return render(request, 'admin_control_panel.html', context)


@csrf_protect
@require_http_methods(["POST"])
def admin_ban_user_panel(request):
    """Ban a user from admin control panel"""
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('/')
    
    email = request.POST.get('email')
    try:
        user = User.objects.get(email=email)
        user.is_flagged = True
        user.save()
        messages.success(request, f'User {user.name} has been banned.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admin_control_panel')


@csrf_protect
@require_http_methods(["POST"])
def admin_unban_user_panel(request):
    """Unban a user from admin control panel"""
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('/')
    
    email = request.POST.get('email')
    try:
        user = User.objects.get(email=email)
        user.is_flagged = False
        user.save()
        messages.success(request, f'User {user.name} has been unbanned.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admin_control_panel')


@csrf_protect
@require_http_methods(["POST"])
def admin_delete_post_panel(request, post_id):
    """Delete a flagged post from admin control panel"""
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('/')
    
    from posts.models import Post
    try:
        post = get_object_or_404(Post, id=post_id)
        post_content = post.content[:50] + "..." if len(post.content) > 50 else post.content
        post.delete()
        messages.success(request, f'Post deleted: "{post_content}"')
    except Exception as e:
        messages.error(request, f'Error deleting post: {str(e)}')
    
    return redirect('admin_control_panel')


@csrf_protect
@require_http_methods(["POST"])
def admin_dismiss_flags_panel(request, post_id):
    """Dismiss all flags for a post from admin control panel"""
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('/')
    
    from posts.models import Post, PostFlag
    try:
        post = get_object_or_404(Post, id=post_id)
        flag_count = post.flag_count()
        PostFlag.objects.filter(post=post).delete()
        messages.success(request, f'Dismissed {flag_count} flag(s) for post.')
    except Exception as e:
        messages.error(request, f'Error dismissing flags: {str(e)}')
    
    return redirect('admin_control_panel')


@csrf_protect
@require_http_methods(["POST"])
def admin_ban_and_delete_panel(request, post_id):
    """Ban user and delete their post from admin control panel"""
    if not request.session.get('is_admin', False):
        messages.error(request, 'Forbidden: Admin access required')
        return redirect('/')
    
    from posts.models import Post
    try:
        post = get_object_or_404(Post, id=post_id)
        target_user = post.author
        post_content = post.content[:50] + "..." if len(post.content) > 50 else post.content
        
        # Ban the user
        target_user.is_flagged = True
        target_user.save()
        
        # Delete the post
        post.delete()
        
        messages.success(request, f'User "{target_user.name}" has been banned and their post deleted: "{post_content}"')
    except Exception as e:
        messages.error(request, f'Error banning user and deleting post: {str(e)}')
    
    return redirect('admin_control_panel')
