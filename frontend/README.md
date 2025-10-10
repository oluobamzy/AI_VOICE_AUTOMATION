# AI Voice Automation Frontend

A beautiful, modern web interface for the AI Voice Automation platform.

## Features

- 🎨 **Modern Design**: Clean, responsive interface with your custom logo
- 🚀 **Real-time Processing**: Live status updates for AI processing tasks
- 📤 **Multiple Upload Methods**: File upload or URL download (YouTube, etc.)
- 🤖 **AI Integration**: OpenAI transcription, ElevenLabs voice, D-ID avatars
- 📊 **Project Management**: View and manage your processed videos
- 🔄 **Live Status**: Real-time backend service monitoring

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Tailwind CSS with custom animations
- **Icons**: Font Awesome 6
- **Backend Integration**: FastAPI REST API
- **Real-time Updates**: Fetch API with async/await

## Files Structure

```
frontend/
├── index.html          # Main application HTML
├── app.js             # JavaScript application logic
├── styles.css         # Custom CSS and animations
└── README.md          # This file
```

## Features Overview

### 1. Video Upload
- **File Upload**: Drag & drop or click to select video files
- **URL Download**: Download videos from YouTube, Vimeo, etc.
- **Validation**: File type and size validation (100MB limit)

### 2. AI Processing Options
- **Transcription**: AI-powered speech-to-text using OpenAI Whisper
- **Voice Generation**: Text-to-speech using ElevenLabs
- **Avatar Creation**: AI avatar videos using D-ID

### 3. Real-time Monitoring
- **Processing Status**: Live progress updates for each AI task
- **Service Health**: Backend service connectivity indicators
- **Project Gallery**: View completed projects and results

### 4. User Experience
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Loading States**: Beautiful loading animations and progress bars
- **Notifications**: Toast notifications for user feedback
- **Accessibility**: Keyboard navigation and screen reader support

## API Integration

The frontend connects to your FastAPI backend at `http://localhost:8000/api/v1` with the following endpoints:

- `GET /health` - Backend health check
- `POST /videos/upload` - File upload
- `POST /videos/download` - URL download
- `GET /videos` - List projects
- `POST /videos/{id}/transcribe` - AI transcription
- `POST /videos/{id}/generate-voice` - Voice generation
- `POST /videos/{id}/create-avatar` - Avatar creation

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Development

The frontend is served directly by your FastAPI backend:

1. **Start Backend**: `python run.py`
2. **Access Frontend**: `http://localhost:8000`
3. **API Docs**: `http://localhost:8000/docs`

## Customization

### Logo
The logo is embedded as an SVG in the CSS. To update:
1. Replace the `background` URL in `.logo-container` class in `styles.css`
2. Or update the SVG data directly

### Colors
Main color scheme is defined in Tailwind classes:
- Primary: Blue (`blue-600`, `blue-700`)
- Secondary: Purple (`purple-600`, `purple-700`)
- Success: Green (`green-500`, `green-600`)
- Error: Red (`red-500`, `red-600`)

### Animations
Custom animations are defined in `styles.css`:
- Logo floating animation
- Card hover effects
- Loading spinners
- Progress bars
- Notifications

## Production Deployment

For production deployment:

1. **Minify Assets**: Use tools like Terser for JavaScript and cssnano for CSS
2. **CDN**: Serve static assets from a CDN
3. **Service Worker**: Add for offline functionality
4. **Security**: Implement Content Security Policy (CSP)

## Accessibility Features

- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ High contrast mode support
- ✅ Reduced motion support
- ✅ Focus indicators
- ✅ ARIA labels

## Performance Optimizations

- ✅ Lazy loading for projects
- ✅ Debounced API calls
- ✅ Optimized animations
- ✅ Efficient DOM updates
- ✅ Progressive enhancement

## Security

- ✅ Input validation
- ✅ XSS protection
- ✅ CSRF protection via backend
- ✅ Secure API communication
- ✅ No sensitive data in localStorage

## Future Enhancements

- [ ] Dark mode toggle
- [ ] Batch processing
- [ ] Advanced project filters
- [ ] Export/import projects
- [ ] Video preview player
- [ ] Collaboration features
- [ ] Advanced settings panel
- [ ] Real-time collaboration
- [ ] Push notifications
- [ ] Offline support

## Support

Your AI Voice Automation platform is now ready with a complete, production-ready frontend that showcases all the powerful AI capabilities of your backend system!