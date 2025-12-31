/**
 * Freedom US Tax Return - Web Application JavaScript
 */

// Global app object
const TaxApp = {
    // Configuration
    config: {
        apiBaseUrl: '',
        currentStep: 0,
        isMobile: false
    },

    // Initialize the application
    init: function() {
        this.detectMobile();
        this.setupEventListeners();
        this.setupFormValidation();
        this.updateUI();
    },

    // Detect if user is on mobile device
    detectMobile: function() {
        this.config.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        if (this.config.isMobile) {
            document.body.classList.add('mobile-device');
        }
    },

    // Setup global event listeners
    setupEventListeners: function() {
        // Handle online/offline status
        window.addEventListener('online', this.handleOnline.bind(this));
        window.addEventListener('offline', this.handleOffline.bind(this));

        // Handle browser back/forward buttons
        window.addEventListener('popstate', this.handleNavigation.bind(this));

        // Handle form submissions
        document.addEventListener('submit', this.handleFormSubmit.bind(this));

        // Handle mobile-specific gestures
        if (this.config.isMobile) {
            this.setupMobileGestures();
        }
    },

    // Setup mobile gesture handling
    setupMobileGestures: function() {
        let startX, startY;

        document.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        document.addEventListener('touchend', function(e) {
            if (!startX || !startY) return;

            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            const diffX = startX - endX;
            const diffY = startY - endY;

            // Swipe detection (minimum 50px movement)
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                if (diffX > 0) {
                    // Swipe left - next step
                    TaxApp.navigateNext();
                } else {
                    // Swipe right - previous step
                    TaxApp.navigatePrevious();
                }
            }
        });
    },

    // Setup form validation
    setupFormValidation: function() {
        // Add real-time validation to all forms
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('blur', this.validateField.bind(this));
                input.addEventListener('input', this.clearFieldError.bind(this));
            });
        });
    },

    // Validate individual field
    validateField: function(e) {
        const field = e.target;
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        // Required field validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
        }

        // SSN validation
        if (field.id === 'ssn' && value) {
            const ssnRegex = /^\d{3}-\d{2}-\d{4}$/;
            if (!ssnRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid SSN (XXX-XX-XXXX)';
            }
        }

        // Phone validation
        if (field.type === 'tel' && value) {
            const phoneRegex = /^\(\d{3}\) \d{3}-\d{4}$/;
            if (!phoneRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid phone number';
            }
        }

        // ZIP code validation
        if (field.id === 'zip_code' && value) {
            const zipRegex = /^\d{5}(-\d{4})?$/;
            if (!zipRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid ZIP code';
            }
        }

        // Date validation
        if (field.type === 'date' && value) {
            const date = new Date(value);
            const now = new Date();
            if (date > now) {
                isValid = false;
                errorMessage = 'Date cannot be in the future';
            }
        }

        // Update field appearance
        if (!isValid) {
            field.classList.add('is-invalid');
            this.showFieldError(field, errorMessage);
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }

        return isValid;
    },

    // Show field error
    showFieldError: function(field, message) {
        // Remove existing error
        this.clearFieldError({ target: field });

        // Create error element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.textContent = message;

        // Insert after field
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    },

    // Clear field error
    clearFieldError: function(e) {
        const field = e.target;
        field.classList.remove('is-invalid', 'is-valid');

        const errorElement = field.parentNode.querySelector('.invalid-feedback');
        if (errorElement) {
            errorElement.remove();
        }
    },

    // Handle form submission
    handleFormSubmit: function(e) {
        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);
        const data = {};

        // Validate all fields
        let isFormValid = true;
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (!this.validateField({ target: input })) {
                isFormValid = false;
            }
            data[input.name || input.id] = input.value;
        });

        if (!isFormValid) {
            this.showAlert('Please correct the errors below', 'danger');
            return;
        }

        // Show loading state
        this.showLoading(form);

        // Submit form data
        const url = form.getAttribute('action') || window.location.pathname;
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            this.hideLoading(form);

            if (result.success) {
                this.showAlert('Information saved successfully!', 'success');

                // Navigate to next step after short delay
                setTimeout(() => {
                    this.navigateNext();
                }, 1000);
            } else {
                this.showAlert(result.error || 'An error occurred', 'danger');
            }
        })
        .catch(error => {
            this.hideLoading(form);
            console.error('Form submission error:', error);
            this.showAlert('Network error. Please try again.', 'danger');
        });
    },

    // Navigation methods
    navigateNext: function() {
        const currentPath = window.location.pathname;
        const nextPaths = {
            '/personal-info': '/filing-status',
            '/filing-status': '/income',
            '/income': '/deductions',
            '/deductions': '/credits',
            '/credits': '/payments',
            '/payments': '/review'
        };

        const nextPath = nextPaths[currentPath];
        if (nextPath) {
            window.location.href = nextPath;
        }
    },

    navigatePrevious: function() {
        const currentPath = window.location.pathname;
        const prevPaths = {
            '/filing-status': '/personal-info',
            '/income': '/filing-status',
            '/deductions': '/income',
            '/credits': '/deductions',
            '/payments': '/credits',
            '/review': '/payments'
        };

        const prevPath = prevPaths[currentPath];
        if (prevPath) {
            window.location.href = prevPath;
        }
    },

    // Handle browser navigation
    handleNavigation: function(e) {
        // Update progress indicators
        this.updateProgress();
    },

    // Update UI elements
    updateUI: function() {
        this.updateProgress();
        this.updateMobileUI();
    },

    // Update progress indicators
    updateProgress: function() {
        const path = window.location.pathname;
        const steps = {
            '/personal-info': 1,
            '/filing-status': 2,
            '/income': 3,
            '/deductions': 4,
            '/credits': 5,
            '/payments': 6,
            '/review': 7
        };

        const currentStep = steps[path] || 0;
        const progressPercent = (currentStep / 6) * 100;

        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = progressPercent + '%';
            progressBar.setAttribute('aria-valuenow', currentStep);
        }

        const stepText = document.querySelector('.text-muted');
        if (stepText && currentStep > 0) {
            stepText.textContent = `Step ${currentStep} of 6`;
        }
    },

    // Update mobile-specific UI
    updateMobileUI: function() {
        if (!this.config.isMobile) return;

        // Add mobile-specific classes and adjustments
        document.body.classList.add('mobile-optimized');

        // Adjust viewport for mobile
        const viewport = document.querySelector('meta[name=viewport]');
        if (viewport) {
            viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
        }
    },

    // Show loading state
    showLoading: function(element) {
        const submitBtn = element.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Saving...';
        }
    },

    // Hide loading state
    hideLoading: function(element) {
        const submitBtn = element.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Continue <i class="fas fa-arrow-right"></i>';
        }
    },

    // Show alert message
    showAlert: function(message, type = 'info') {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alertDiv);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    },

    // Handle online/offline status
    handleOnline: function() {
        this.showAlert('Connection restored', 'success');
    },

    handleOffline: function() {
        this.showAlert('You are currently offline. Some features may not be available.', 'warning');
    },

    // Utility methods
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    formatPercent: function(value) {
        return (value * 100).toFixed(2) + '%';
    },

    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    TaxApp.init();
});

// Export for global access
window.TaxApp = TaxApp;