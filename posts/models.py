from django.db import models

class Post(models.Model):
    #The user who wrote the post
    author = models.ForeignKey('users.User', on_delete=models.CASCADE)
    #Text content of the post
    content = models.TextField(max_length=1000)
    #Timestamp automatically set when post is created
    created_at = models.DateTimeField(auto_now_add=True)
    #moderation flag
    is_flagged = models.BooleanField(default=False)

    class Meta:
        #show newest first
        ordering = ['-created_at']  
    def __str__(self):
        return f"{self.author.email}: {self.content[:30]}"
