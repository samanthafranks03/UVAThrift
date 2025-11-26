// Walkthrough Tour System
class WalkthroughTour {
    constructor(steps, onComplete) {
        this.steps = steps;
        this.currentStep = 0;
        this.onComplete = onComplete;
        this.overlay = null;
        this.tooltip = null;
        this.highlightedElement = null;
        
        this.init();
    }
    
    init() {
        // Create overlay
        this.overlay = document.createElement('div');
        this.overlay.className = 'walkthrough-overlay';
        document.body.appendChild(this.overlay);
        
        // Create tooltip
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'walkthrough-tooltip';
        document.body.appendChild(this.tooltip);
        
        // Add click handler to overlay
        this.overlay.addEventListener('click', () => this.skip());
    }
    
    start() {
        this.currentStep = 0;
        this.showStep();
    }
    
    showStep() {
        if (this.currentStep >= this.steps.length) {
            this.complete();
            return;
        }
        
        const step = this.steps[this.currentStep];
        
        // Show overlay
        this.overlay.classList.add('active');
        
        // Highlight target element
        this.highlightElement(step.target);
        
        // Position and show tooltip
        this.positionTooltip(step);
        
        // Update tooltip content
        this.updateTooltipContent(step);
        
        this.tooltip.classList.add('active');
    }
    
    highlightElement(selector) {
        // Remove previous highlight
        if (this.highlightedElement) {
            this.highlightedElement.classList.remove('walkthrough-highlight');
        }
        
        // Add new highlight
        if (selector) {
            const element = document.querySelector(selector);
            if (element) {
                element.classList.add('walkthrough-highlight');
                this.highlightedElement = element;
                
                // Scroll element into view
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }
    
    positionTooltip(step) {
        if (!step.target) {
            // Center tooltip if no target
            this.tooltip.style.top = '50%';
            this.tooltip.style.left = '50%';
            this.tooltip.style.transform = 'translate(-50%, -50%)';
            return;
        }
        
        const element = document.querySelector(step.target);
        if (!element) return;
        
        const rect = element.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        
        // Remove any existing arrow
        const existingArrow = this.tooltip.querySelector('.walkthrough-arrow');
        if (existingArrow) {
            existingArrow.remove();
        }
        
        // Position based on available space
        const position = step.position || 'bottom';
        let top, left;
        let arrowClass = '';
        
        switch(position) {
            case 'top':
                top = rect.top - tooltipRect.height - 20;
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                arrowClass = 'arrow-bottom';
                break;
            case 'bottom':
                top = rect.bottom + 20;
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                arrowClass = 'arrow-top';
                break;
            case 'left':
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                left = rect.left - tooltipRect.width - 20;
                arrowClass = 'arrow-right';
                break;
            case 'right':
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                left = rect.right + 20;
                arrowClass = 'arrow-left';
                break;
        }
        
        // Ensure tooltip stays within viewport
        const padding = 10;
        if (left < padding) left = padding;
        if (left + tooltipRect.width > window.innerWidth - padding) {
            left = window.innerWidth - tooltipRect.width - padding;
        }
        if (top < padding) top = padding;
        if (top + tooltipRect.height > window.innerHeight - padding) {
            top = window.innerHeight - tooltipRect.height - padding;
        }
        
        this.tooltip.style.top = top + 'px';
        this.tooltip.style.left = left + 'px';
        this.tooltip.style.transform = 'none';
        
        // Add arrow
        if (arrowClass) {
            const arrow = document.createElement('div');
            arrow.className = 'walkthrough-arrow ' + arrowClass;
            this.tooltip.appendChild(arrow);
        }
    }
    
    updateTooltipContent(step) {
        const isFirst = this.currentStep === 0;
        const isLast = this.currentStep === this.steps.length - 1;
        
        this.tooltip.innerHTML = `
            <h3>${step.title}</h3>
            <p>${step.content}</p>
            <div class="walkthrough-tooltip-footer">
                <div class="walkthrough-progress">
                    Step ${this.currentStep + 1} of ${this.steps.length}
                </div>
                <div class="walkthrough-buttons">
                    <button class="walkthrough-btn walkthrough-btn-skip" onclick="walkthroughTour.skip()">
                        Skip Tour
                    </button>
                    ${!isFirst ? '<button class="walkthrough-btn walkthrough-btn-prev" onclick="walkthroughTour.prev()">Previous</button>' : ''}
                    ${!isLast ? 
                        '<button class="walkthrough-btn walkthrough-btn-next" onclick="walkthroughTour.next()">Next</button>' :
                        '<button class="walkthrough-btn walkthrough-btn-done" onclick="walkthroughTour.complete()">Got it!</button>'
                    }
                </div>
            </div>
        `;
    }
    
    next() {
        this.currentStep++;
        this.showStep();
    }
    
    prev() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep();
        }
    }
    
    skip() {
        if (confirm('Are you sure you want to skip the tour? You can always restart it from your profile settings.')) {
            this.complete();
        }
    }
    
    complete() {
        // Remove highlight
        if (this.highlightedElement) {
            this.highlightedElement.classList.remove('walkthrough-highlight');
        }
        
        // Hide overlay and tooltip
        this.overlay.classList.remove('active');
        this.tooltip.classList.remove('active');
        
        // Call completion callback
        if (this.onComplete) {
            this.onComplete();
        }
        
        // Clean up
        setTimeout(() => {
            this.overlay.remove();
            this.tooltip.remove();
        }, 300);
    }
}

// Global variable to hold the tour instance
let walkthroughTour = null;

// Function to start the walkthrough
function startWalkthrough() {
    // Check if user is logged in (check for profile link in navbar)
    const isLoggedIn = document.querySelector("a[href*='/users/']") !== null;
    
    // Define the steps for the tour
    let steps = [
        {
            target: null,
            title: "Welcome to UVA Thrift! 🎉",
            content: "Let's take a quick tour of the main features. This will only take a minute!",
            position: "center"
        },
        {
            target: ".navbar-brand",
            title: "Your Marketplace",
            content: "UVA Thrift is your platform to buy and sell items within the UVA community. Click the logo anytime to return to the browse page.",
            position: "bottom"
        },
        {
            target: "a[href='/market']",
            title: "Browse Posts",
            content: "This is where you can see all the items for sale. Browse through listings from other students!",
            position: "bottom"
        }
    ];
    
    // Add logged-in user steps
    if (isLoggedIn) {
        steps.push({
            target: "a[href*='/users/']",
            title: "Your Profile",
            content: "Visit your profile to edit your information, view your posts, and manage your account.",
            position: "bottom"
        });
        steps.push({
            target: "a[href*='/messaging/']",
            title: "Messages",
            content: "Connect with buyers and sellers through direct messages. Negotiate prices and arrange meetups!",
            position: "bottom"
        });
        steps.push({
            target: "a[href*='/notifications']",
            title: "Notifications",
            content: "Stay updated with notifications about messages and activity on your posts.",
            position: "bottom"
        });
        steps.push({
            target: "#create-post-form",
            title: "Create a Post",
            content: "Ready to sell something? Write a description, upload an image, and post it to the marketplace!",
            position: "top"
        });
    } else {
        steps.push({
            target: "a[href='/login/']",
            title: "Sign In",
            content: "Sign in with your Google account to create posts, message other users, and manage your profile!",
            position: "bottom"
        });
    }
    
    // Add common steps for all users
    steps.push({
        target: ".posts-grid",
        title: "Recent Posts",
        content: "Scroll through recent listings. Click on a username to view their profile" + (isLoggedIn ? ", or use the flag button to report inappropriate content." : "!"),
        position: "top"
    });
    
    steps.push({
        target: null,
        title: "You're All Set! ✅",
        content: isLoggedIn ? "That's everything you need to know to get started. Happy buying and selling!" : "Sign in to unlock all features and start buying and selling!",
        position: "center"
    });
    
    // Create and start the tour
    walkthroughTour = new WalkthroughTour(steps, function() {
        // Mark walkthrough as complete on the server
        fetch('/users/complete-walkthrough/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        }).then(response => {
            if (response.ok) {
                console.log('Walkthrough marked as complete');
            }
        }).catch(error => {
            console.error('Error marking walkthrough complete:', error);
        });
    });
    
    walkthroughTour.start();
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
