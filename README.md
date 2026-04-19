# UVAThrift
 
A platform for UVA students to donate and exchange furniture, clothes, school supplies, and more! This web application was built with Django and deployed on Heroku.
 
---
 
## About
 
The UVA Community Marketplace connects students who want to give and receive second-hand goods. Users can post listings, message each other, and browse available items all within the UVA community.
 
---
 
## Features
 
### User Accounts
- Google Account login for all users
- Regular and admin user roles (distinguished by email)
- Editable profiles: bio, nickname, profile picture, and interests
- Profile pictures and listing images stored on AWS S3
### Market Page
- Browse all recent listings in a grid layout
- Each listing displays the associated user's name
- Upload images directly with posts
### Messaging
- Direct message any user individually or in a group
- Start a conversation from a listing page or the Messages tab
- View and manage all conversations in one place
### Admin Controls
- View a table of all registered users (name, email, status)
- Ban users who violate the platform's terms of use
- Flag posts with content that violates app policies (visible to all admins)
---
 
## Tech Stack
 
| Layer | Technology |
|---|---|
| Backend | Django |
| Deployment | Heroku |
| File Storage | AWS S3 |
| UI Design | Figma |
| Version Control | GitHub |
 
---
 
## Getting Started
 
### Prerequisites
- Python 3.x
- pip
- A configured Heroku account (for deployment)
- AWS S3 bucket credentials
### Installation
 
```bash
git clone https://github.com/samanthafranks03/UVAThrift.git
cd UVAThrift
pip install -r requirements.txt
```
 
Set up your environment variables (e.g., in a `.env` file):
 
```
SECRET_KEY=your_django_secret_key
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=your_bucket
DATABASE_URL=your_db_url
```
 
Then run:
 
```bash
python manage.py migrate
python manage.py runserver
```
 
---
 
## Development Process
 
Requirements were gathered through:
- **Interviews** — each team member interviewed two UVA students about their second-hand shopping and donating habits
- **Questionnaire** — a standardized set of questions distributed to potential users
- **Artifact analysis** — a review of Facebook Marketplace's features and policies
User stories were written from these findings, uploaded as **GitHub Issues**, and prioritized into sprints.
 
---
 
## Team
 
Developed by a team of UVA students as part of a software engineering course project.
