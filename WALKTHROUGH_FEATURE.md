# User Walkthrough Feature

## Overview
This feature provides an interactive step-by-step walkthrough for new users when they first log in to the UVA Thrift marketplace. The walkthrough highlights key features and helps users get familiar with the platform.

## How it works

### For New Users
1. When a user logs in for the first time (detected by `has_seen_walkthrough=False`), the walkthrough automatically starts
2. An overlay appears with highlighted elements and tooltips explaining each feature
3. Users can navigate through steps using "Next" and "Previous" buttons
4. Users can skip the tour at any time
5. Once completed (or skipped), the walkthrough is marked as seen and won't show again automatically

### For existing users
- Users can manually restart the walkthrough from their profile page
- Click the "🎓 Restart Walkthrough" button on your profile to see the tour again

## Technical Implementation

### Database changes
- added `has_seen_walkthrough` field to the `User` model
- Migration: `users/migrations/0006_user_has_seen_walkthrough.py`

### Files Created/Modified

#### New Files:
1. **`a2_market/static/a2_market/walkthrough.css`** - styling for walkthrough overlay, tooltips, and highlights
2. **`a2_market/static/a2_market/walkthrough.js`** - managing the tour functionality

#### Modified Files:
1. **`users/models.py`** - added `has_seen_walkthrough` field
2. **`users/views.py`** - added `complete_walkthrough` view to mark tour as complete
3. **`users/urls.py`** - added URL route for completing walkthrough
4. **`market/views.py`** - added logic to check if user needs walkthrough
5. **`a2_market/templates/a2_market/base.html`** - included walkthrough CSS/JS and initialization
6. **`users/templates/profile.html`** - added button to restart walkthrough

## Walkthrough Steps

The tour includes 9 steps:

1. **Welcome** - Introduction to UVA Thrift
2. **Navbar Brand** - Explains the logo and home navigation
3. **Browse Posts** - Shows where to view listings
4. **Profile** - Guides to profile management
5. **Messages** - Explains messaging feature
6. **Notifications** - Shows notification system
7. **Create Post** - How to create new listings
8. **Recent Posts** - Browsing and interacting with posts
9. **Completion** - Final message

## Customization

### Adding/Modifying Steps
Edit `a2_market/static/a2_market/walkthrough.js` and modify the `steps` array in `startWalkthrough()`:

```javascript
const steps = [
    {
        target: ".css-selector",  // Element to highlight (or null for centered)
        title: "Step Title",
        content: "Step description",
        position: "bottom"  // top, bottom, left, right, or center
    },
    // Add more steps...
];
```

### Styling
Modify `a2_market/static/a2_market/walkthrough.css` to change:
- Overlay opacity/color
- Tooltip appearance
- Highlight effects
- Button styles

## API Endpoints

### POST `/users/complete-walkthrough/`
Marks the walkthrough as complete for the logged-in user.

**Request:**
```javascript
fetch('/users/complete-walkthrough/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    credentials: 'same-origin'
});
```

**Response:**
```json
{
    "success": true
}
```

## Testing

### Test Walkthrough for New Users:
1. Create a new user account (or set `has_seen_walkthrough=False` in database)
2. Log in
3. Verify walkthrough starts automatically on the home page

### Test Manual Restart:
1. Log in as any user
2. Go to your profile
3. Click "🎓 Restart Walkthrough"
4. Verify tour starts

### Test Skip Functionality:
1. Start walkthrough
2. Click "Skip Tour"
3. Confirm the action
4. Verify walkthrough closes and is marked complete

## Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled
- Responsive design for desktop and mobile

## Future Enhancements
- Add analytics to track which steps users skip
- Create different tours for different user roles (buyers vs sellers)
- Add video tutorials embedded in walkthrough
- Implement contextual help that can be triggered from any page
- Add ability for admins to customize walkthrough steps via admin panel
