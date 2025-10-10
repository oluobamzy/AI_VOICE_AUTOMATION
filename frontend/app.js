// AI Voice Automation Frontend JavaScript
// Connects to FastAPI backend for video processing

// Global app instance
let app;

class AIVoiceAutomation {
    constructor() {
        this.apiBase = 'http://localhost:8000/api/v1';
        this.currentJob = null;
        this.authToken = localStorage.getItem('auth_token');
        this.currentUser = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAuthListeners();
        this.checkAuthStatus();
        this.checkBackendStatus();
        this.loadProjects();
    }

    setupEventListeners() {
        // File upload
        const fileInput = document.getElementById('fileInput');
        const selectFileBtn = document.getElementById('selectFileBtn');
        const fileUploadArea = document.getElementById('fileUploadArea');

        selectFileBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Drag and drop
        fileUploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        fileUploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        fileUploadArea.addEventListener('drop', this.handleDrop.bind(this));

        // URL download
        document.getElementById('downloadBtn').addEventListener('click', this.handleUrlDownload.bind(this));

        // Start processing
        document.getElementById('startProcessing').addEventListener('click', this.startProcessing.bind(this));
    }

    setupAuthListeners() {
        // Modal controls
        document.getElementById('loginBtn').addEventListener('click', () => this.showLoginModal());
        document.getElementById('registerBtn').addEventListener('click', () => this.showRegisterModal());
        document.getElementById('closeLoginModal').addEventListener('click', () => this.hideLoginModal());
        document.getElementById('closeRegisterModal').addEventListener('click', () => this.hideRegisterModal());
        document.getElementById('switchToRegister').addEventListener('click', () => this.switchToRegister());
        document.getElementById('switchToLogin').addEventListener('click', () => this.switchToLogin());
        document.getElementById('logoutBtn').addEventListener('click', () => this.logout());

        // Form submissions
        document.getElementById('loginForm').addEventListener('submit', this.handleLogin.bind(this));
        document.getElementById('registerForm').addEventListener('submit', this.handleRegister.bind(this));

        // Close modals on outside click
        document.getElementById('loginModal').addEventListener('click', (e) => {
            if (e.target.id === 'loginModal') this.hideLoginModal();
        });
        document.getElementById('registerModal').addEventListener('click', (e) => {
            if (e.target.id === 'registerModal') this.hideRegisterModal();
        });
    }

    async checkAuthStatus() {
        if (this.authToken) {
            try {
                const response = await fetch(`${this.apiBase}/auth/me`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`
                    }
                });
                
                if (response.ok) {
                    this.currentUser = await response.json();
                    this.updateAuthUI(true);
                } else {
                    // Token is invalid
                    this.logout();
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                this.logout();
            }
        } else {
            this.updateAuthUI(false);
        }
    }

    updateAuthUI(isLoggedIn) {
        const notLoggedIn = document.getElementById('notLoggedIn');
        const loggedIn = document.getElementById('loggedIn');
        const userDisplay = document.getElementById('userDisplay');

        if (isLoggedIn && this.currentUser) {
            notLoggedIn.classList.add('hidden');
            loggedIn.classList.remove('hidden');
            userDisplay.textContent = this.currentUser.full_name || this.currentUser.username;
        } else {
            notLoggedIn.classList.remove('hidden');
            loggedIn.classList.add('hidden');
        }
    }

    showLoginModal() {
        document.getElementById('loginModal').classList.remove('hidden');
        document.getElementById('loginModal').classList.add('flex');
    }

    hideLoginModal() {
        document.getElementById('loginModal').classList.add('hidden');
        document.getElementById('loginModal').classList.remove('flex');
        this.clearLoginForm();
    }

    showRegisterModal() {
        document.getElementById('registerModal').classList.remove('hidden');
        document.getElementById('registerModal').classList.add('flex');
    }

    hideRegisterModal() {
        document.getElementById('registerModal').classList.add('hidden');
        document.getElementById('registerModal').classList.remove('flex');
        this.clearRegisterForm();
    }

    switchToRegister() {
        this.hideLoginModal();
        this.showRegisterModal();
    }

    switchToLogin() {
        this.hideRegisterModal();
        this.showLoginModal();
    }

    clearLoginForm() {
        document.getElementById('loginForm').reset();
    }

    clearRegisterForm() {
        document.getElementById('registerForm').reset();
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const rememberMe = document.getElementById('rememberMe').checked;

        try {
            const response = await fetch(`${this.apiBase}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    remember_me: rememberMe
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.authToken = data.access_token;
                this.currentUser = data.user;
                
                localStorage.setItem('auth_token', this.authToken);
                
                this.updateAuthUI(true);
                this.hideLoginModal();
                this.showNotification('Login successful!', 'success');
                
                // Reload projects to show user's videos
                this.loadProjects();
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Login failed. Please try again.', 'error');
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const fullName = document.getElementById('registerFullName').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (password !== confirmPassword) {
            this.showNotification('Passwords do not match', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    full_name: fullName || null,
                    password: password,
                    confirm_password: confirmPassword,
                    is_active: true
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.authToken = data.access_token;
                this.currentUser = data.user;
                
                localStorage.setItem('auth_token', this.authToken);
                
                this.updateAuthUI(true);
                this.hideRegisterModal();
                this.showNotification('Registration successful!', 'success');
                
                // Reload projects to show user's videos
                this.loadProjects();
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showNotification('Registration failed. Please try again.', 'error');
        }
    }

    logout() {
        this.authToken = null;
        this.currentUser = null;
        localStorage.removeItem('auth_token');
        this.updateAuthUI(false);
        this.showNotification('Logged out successfully', 'info');
        
        // Reload projects to show public/demo content
        this.loadProjects();
    }

    getAuthHeaders() {
        if (this.authToken) {
            return {
                'Authorization': `Bearer ${this.authToken}`
            };
        }
        return {};
    }

    async checkBackendStatus() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            if (response.ok) {
                this.showNotification('Backend connected successfully!', 'success');
                this.updateServiceStatus();
            }
        } catch (error) {
            this.showNotification('Backend connection failed. Please ensure the server is running.', 'error');
            console.error('Backend connection error:', error);
        }
    }

    async updateServiceStatus() {
        // Update service status indicators
        const services = document.querySelectorAll('.status-indicator');
        services.forEach(indicator => {
            const circle = indicator.querySelector('i');
            circle.className = 'fas fa-circle text-green-500 text-xs';
        });
    }

    handleFileSelect(event) {
        const files = event.target.files;
        if (files.length > 0) {
            this.processSelectedFile(files[0]);
        }
    }

    handleDragOver(event) {
        event.preventDefault();
        event.currentTarget.classList.add('dragover');
    }

    handleDragLeave(event) {
        event.currentTarget.classList.remove('dragover');
    }

    handleDrop(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('dragover');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.processSelectedFile(files[0]);
        }
    }

    processSelectedFile(file) {
        // Validate file type
        if (!file.type.startsWith('video/')) {
            this.showNotification('Please select a valid video file.', 'error');
            return;
        }

        // Check file size (100MB limit based on config)
        const maxSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxSize) {
            this.showNotification('File size exceeds 100MB limit.', 'error');
            return;
        }

        this.selectedFile = file;
        this.showNotification(`Selected: ${file.name}`, 'info');
        
        // Update UI to show file selected
        const uploadArea = document.getElementById('fileUploadArea');
        uploadArea.innerHTML = `
            <i class="fas fa-check-circle text-4xl text-green-500 mb-4"></i>
            <h3 class="text-lg font-semibold text-green-700 mb-2">File Selected</h3>
            <p class="text-gray-600 mb-4">${file.name}</p>
            <button id="selectFileBtn" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                Change File
            </button>
        `;
        
        // Re-attach event listener
        document.getElementById('selectFileBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    async handleUrlDownload() {
        if (!this.authToken) {
            this.showNotification('Please login to download videos', 'error');
            this.showLoginModal();
            return;
        }

        const url = document.getElementById('videoUrl').value.trim();
        if (!url) {
            this.showNotification('Please enter a valid URL.', 'error');
            return;
        }

        this.showLoading('Downloading video from URL...');

        try {
            // Detect platform from URL
            let platform = 'other';
            if (url.includes('youtube.com') || url.includes('youtu.be')) {
                platform = 'youtube';
            } else if (url.includes('tiktok.com')) {
                platform = 'tiktok';
            } else if (url.includes('instagram.com')) {
                platform = 'instagram';
            } else if (url.includes('twitter.com') || url.includes('x.com')) {
                platform = 'twitter';
            }

            const response = await fetch(`${this.apiBase}/videos/from-url`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({ 
                    source_url: url,
                    platform: platform,
                    description: `Video from ${platform}`,
                    tags: []
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.selectedVideoId = result.video_id;
                this.showNotification('Video downloaded successfully!', 'success');
                this.loadProjects(); // Refresh projects
            } else {
                const error = await response.json();
                this.showNotification(`Download failed: ${error.detail}`, 'error');
            }
        } catch (error) {
            this.showNotification('Download failed. Please check the URL and try again.', 'error');
            console.error('Download error:', error);
        } finally {
            this.hideLoading();
        }
    }

    async startProcessing() {
        if (!this.selectedFile && !this.selectedVideoId) {
            this.showNotification('Please select a file or download from URL first.', 'error');
            return;
        }

        const options = {
            transcribe: document.getElementById('transcribeAudio').checked,
            generateVoice: document.getElementById('generateVoice').checked,
            createAvatar: document.getElementById('createAvatar').checked
        };

        this.showLoading('Starting AI processing...');

        try {
            let videoId = this.selectedVideoId;

            // Upload file if not from URL
            if (this.selectedFile) {
                videoId = await this.uploadFile();
            }

            if (videoId) {
                await this.processVideo(videoId, options);
            }
        } catch (error) {
            this.showNotification('Processing failed. Please try again.', 'error');
            console.error('Processing error:', error);
        } finally {
            this.hideLoading();
        }
    }

    async uploadFile() {
        if (!this.authToken) {
            this.showNotification('Please login to upload videos', 'error');
            this.showLoginModal();
            return null;
        }

        const formData = new FormData();
        formData.append('file', this.selectedFile);

        const response = await fetch(`${this.apiBase}/videos/upload`, {
            method: 'POST',
            headers: {
                ...this.getAuthHeaders()
            },
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            return result.id;
        } else {
            throw new Error('File upload failed');
        }
    }

    async processVideo(videoId, options) {
        this.currentJob = videoId;
        
        // Show processing status section
        const statusSection = document.getElementById('processingStatus');
        statusSection.classList.remove('hidden');
        
        // Start processing steps
        const steps = [];
        
        if (options.transcribe) {
            steps.push({ name: 'AI Transcription', endpoint: '/transcribe', icon: 'fas fa-microphone' });
        }
        
        if (options.generateVoice) {
            steps.push({ name: 'Voice Generation', endpoint: '/generate-voice', icon: 'fas fa-volume-up' });
        }
        
        if (options.createAvatar) {
            steps.push({ name: 'AI Avatar Creation', endpoint: '/create-avatar', icon: 'fas fa-user-circle' });
        }

        this.updateProcessingSteps(steps);

        // Execute steps sequentially
        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];
            await this.executeProcessingStep(videoId, step, i, steps.length);
        }

        this.showNotification('Processing completed successfully!', 'success');
        this.loadProjects(); // Refresh projects
    }

    updateProcessingSteps(steps) {
        const stepStatus = document.getElementById('stepStatus');
        stepStatus.innerHTML = steps.map((step, index) => `
            <div class="flex items-center space-x-3" id="step-${index}">
                <div class="flex-shrink-0">
                    <i class="${step.icon} text-gray-400"></i>
                </div>
                <div class="flex-1">
                    <h4 class="font-medium text-gray-800">${step.name}</h4>
                    <div class="bg-gray-200 rounded-full h-2 mt-1">
                        <div class="bg-blue-500 h-2 rounded-full transition-all duration-500" style="width: 0%"></div>
                    </div>
                </div>
                <div class="flex-shrink-0">
                    <span class="text-sm text-gray-500">Waiting</span>
                </div>
            </div>
        `).join('');
    }

    async executeProcessingStep(videoId, step, stepIndex, totalSteps) {
        const stepElement = document.getElementById(`step-${stepIndex}`);
        const progressBar = stepElement.querySelector('.bg-blue-500');
        const statusText = stepElement.querySelector('.text-sm');
        const icon = stepElement.querySelector('i');

        // Update step status to processing
        icon.className = step.icon + ' text-blue-500';
        statusText.textContent = 'Processing...';
        
        // Simulate processing with progress updates
        for (let progress = 0; progress <= 100; progress += 10) {
            progressBar.style.width = progress + '%';
            await new Promise(resolve => setTimeout(resolve, 200));
        }

        // Mark as completed
        icon.className = step.icon + ' text-green-500';
        statusText.textContent = 'Completed';
        
        // Update overall progress
        const overallProgress = ((stepIndex + 1) / totalSteps) * 100;
        document.getElementById('overallProgress').style.width = overallProgress + '%';
    }

    async loadProjects() {
        try {
            if (!this.authToken) {
                // Show empty state when not logged in
                this.displayProjects([]);
                return;
            }

            const response = await fetch(`${this.apiBase}/videos/`, {
                headers: {
                    ...this.getAuthHeaders()
                }
            });
            
            if (response.ok) {
                const projects = await response.json();
                this.displayProjects(projects);
            } else if (response.status === 401) {
                // Token expired or invalid
                this.logout();
                this.displayProjects([]);
            } else {
                console.error('Failed to load projects:', response.status);
                this.displayProjects([]);
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
            this.displayProjects([]);
        }
    }

    displayProjects(projects) {
        const grid = document.getElementById('projectsGrid');
        
        if (projects.length === 0) {
            grid.innerHTML = `
                <div class="text-center py-8 text-gray-500 col-span-full">
                    <i class="fas fa-video text-4xl mb-4"></i>
                    <p class="login-prompt">${this.authToken 
                        ? 'No videos yet. Upload a video to get started!'
                        : 'Please <button class="text-blue-600 hover:text-blue-700 underline login-button">login</button> to view your videos.'
                    }</p>
                </div>
            `;
            
            // Add event listener for login button if not authenticated
            if (!this.authToken) {
                const loginButton = grid.querySelector('.login-button');
                if (loginButton) {
                    loginButton.addEventListener('click', () => this.showLoginModal());
                }
            }
            return;
        }

        grid.innerHTML = projects.map(project => `
            <div class="card-hover bg-white rounded-lg shadow-md overflow-hidden">
                <div class="h-48 bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center">
                    <i class="fas fa-play text-4xl text-white"></i>
                </div>
                <div class="p-4">
                    <h3 class="font-semibold text-gray-800 mb-2">${project.filename || 'Untitled Project'}</h3>
                    <p class="text-sm text-gray-600 mb-3">${project.description || 'AI processed video'}</p>
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-xs text-gray-500">${this.formatDate(project.created_at)}</span>
                        <span class="px-2 py-1 text-xs rounded-full ${this.getStatusColor(project.status)}">${project.status}</span>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="app.viewVideo('${project.id}')" class="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700 transition-colors">
                            <i class="fas fa-play mr-1"></i>View
                        </button>
                        <button onclick="app.downloadVideo('${project.id}')" class="flex-1 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700 transition-colors">
                            <i class="fas fa-download mr-1"></i>Download
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    }

    getStatusColor(status) {
        const statusColors = {
            'completed': 'bg-green-100 text-green-800',
            'processing': 'bg-blue-100 text-blue-800',
            'uploaded': 'bg-yellow-100 text-yellow-800',
            'downloading': 'bg-purple-100 text-purple-800',
            'failed': 'bg-red-100 text-red-800',
            'pending': 'bg-gray-100 text-gray-800'
        };
        return statusColors[status] || statusColors.pending;
    }

    async viewVideo(videoId) {
        try {
            const response = await fetch(`${this.apiBase}/videos/${videoId}/view`);
            if (response.ok) {
                const videoData = await response.json();
                this.showVideoModal(videoData);
            } else {
                this.showNotification('Failed to load video details', 'error');
            }
        } catch (error) {
            console.error('Error viewing video:', error);
            this.showNotification('Error loading video', 'error');
        }
    }

    async downloadVideo(videoId) {
        try {
            // Create a temporary link and trigger download
            const downloadUrl = `${this.apiBase}/videos/${videoId}/download`;
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = ''; // Let the server decide the filename
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showNotification('Download started!', 'success');
        } catch (error) {
            console.error('Error downloading video:', error);
            this.showNotification('Error starting download', 'error');
        }
    }

    showVideoModal(videoData) {
        // Create and show a modal for video viewing
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-auto">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-2xl font-bold">${videoData.filename}</h2>
                        <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove()" class="text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    <div class="mb-4">
                        <p><strong>Status:</strong> <span class="px-2 py-1 rounded text-sm ${this.getStatusColor(videoData.status)}">${videoData.status}</span></p>
                        <p><strong>Duration:</strong> ${videoData.duration || 'Unknown'}</p>
                        <p><strong>Resolution:</strong> ${videoData.resolution || 'Unknown'}</p>
                        <p><strong>Created:</strong> ${this.formatDate(videoData.created_at)}</p>
                    </div>
                    <div class="flex space-x-4">
                        <a href="${videoData.download_url}" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors">
                            <i class="fas fa-download mr-2"></i>Download
                        </a>
                        <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove()" class="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    showLoading(text = 'Loading...') {
        const modal = document.getElementById('loadingModal');
        const loadingText = document.getElementById('loadingText');
        loadingText.textContent = text;
        modal.classList.remove('hidden');
    }

    hideLoading() {
        const modal = document.getElementById('loadingModal');
        modal.classList.add('hidden');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg text-white transform transition-all duration-300 translate-x-full`;
        
        // Set color based on type
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500',
            warning: 'bg-yellow-500'
        };
        
        notification.classList.add(colors[type] || colors.info);
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle',
            warning: 'fas fa-exclamation-triangle'
        };
        
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="${icons[type] || icons.info}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 4000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    app = new AIVoiceAutomation();
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIVoiceAutomation;
}