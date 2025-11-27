from django.db import models

from taggit.managers import TaggableManager

class Post(models.Model):
    #The user who wrote the post
    author = models.ForeignKey('users.User', on_delete=models.CASCADE)
    #Name of the item being listed
    title = models.CharField(max_length=120, default="Unnamed Item", blank=True)
    #Text content of the post
    content = models.TextField(max_length=1000)
    #Pickup location for the item
    location = models.CharField(max_length=120, default="Location not provided", blank=True)
    #Timestamp automatically set when post is created
    created_at = models.DateTimeField(auto_now_add=True)
    # Optional image for post; will be required at the form level
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    #moderation flag
    is_flagged = models.BooleanField(default=False)

    # Tags handled by taggit
    tags = TaggableManager()

    class Meta:
        #show newest first
        ordering = ['-created_at']  
    
    def __str__(self):
        return f"{self.author.email}: {self.content[:30]}"
    
    def flag_count(self):
        #Returns the number of users who have flagged this post
        return self.postflag_set.count()
    
    def is_flagged_by_user(self, user):
        #Check if a specific user has flagged this post
        return self.postflag_set.filter(user=user).exists()


class PostFlag(models.Model):
    #Model to track which users have flagged which posts
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')  # Prevent duplicate flags from same user
        
    def __str__(self):
        return f"{self.user.email} flagged post {self.post.id}"
