# PM Login Backend

A comprehensive Python backend for the PM Login Electron application that **authenticates with the original server** at `https://dev.pmbackend.site` while providing local proxy and profile management.

## 🏗️ Project Structure

```
pmlogin-back/
├── core/                    # Core application modules
│   ├── __init__.py
│   ├── auth.py             # JWT authentication & password hashing
│   ├── database.py         # Database configuration & connection
│   ├── models.py           # SQLAlchemy database models
│   └── schemas.py          # Pydantic request/response schemas
├── services/               # Business logic services
│   ├── __init__.py
│   ├── original_server_service.py  # Original server communication
│   ├── proxy_service.py    # Proxy management logic
│   └── profile_service.py  # Profile management logic
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── setup.py           # Demo environment setup
├── client/                 # Frontend integration
│   └── pm_client.js       # JavaScript client for frontend
├── main.py                # FastAPI application
├── app.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
└── README.md             # This file
```

## 🔐 Authentication Flow

This backend acts as a **middleware/proxy** between your frontend and the original PM Login server:

1. **User Login**: Forwards credentials to `https://dev.pmbackend.site/login`
2. **Authentication**: Validates with the original server
3. **Local Session**: Creates local JWT token for subsequent requests
4. **Data Storage**: Stores user sessions, proxies, and profiles locally
5. **Fallback**: Provides offline functionality when original server is unavailable

## Features

### 🔐 Authentication (Proxied to Original Server)
- User login forwarded to `https://dev.pmbackend.site/login`
- User registration forwarded to original server
- Hardware ID (HWID) validation maintained
- Password change forwarded to original server
- Local JWT tokens for session management

### 🌐 Proxy Management (Local)
- Add, update, delete proxies (stored locally)
- Bulk proxy operations
- Proxy testing and validation
- Import proxies from text
- Proxy statistics and analytics
- Support for HTTP, HTTPS, SOCKS4, SOCKS5
- Tag-based organization
- Concurrent proxy testing

### 👤 Profile Management (Local)
- Create, update, delete profiles (stored locally)
- Profile grouping and tagging
- Bulk profile operations
- Profile duplication
- Start/stop profile tracking
- Cloud sharing status
- Profile statistics

### 📊 System Information (Hybrid)
- Server status from original server with local fallback
- App update notifications from original server
- Subscription plans from original server
- Health check endpoints

## Installation

1. **Navigate to the backend directory:**
   ```bash
   cd pmlogin-back
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup demo environment:**
   ```bash
   python utils/setup.py
   ```

## Running the Server

### Development Mode
```bash
python app.py
```

### Production Mode
```bash
# Set DEBUG=False in .env first
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Configuration

Edit the `.env` file with your settings:

```env
# Database
DATABASE_URL=sqlite:///./pmlogin.db

# JWT Settings
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App Settings
APP_NAME=PM Login Backend
VERSION=1.0.0
DEBUG=True
HOST=0.0.0.0
PORT=8000

# CORS Settings
ALLOWED_ORIGINS=*
```

## Running the Server

### Development Mode
```bash
python start.py
```

### Production Mode
```bash
# Set DEBUG=False in .env first
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Using Docker (Optional)
```bash
# Build image
docker build -t pmlogin-backend .

# Run container
docker run -p 8000:8000 pmlogin-backend
```

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `POST /refresh` - Refresh token
- `GET /api/user` - Get current user
- `POST /change-password` - Change password

### Proxy Management
- `GET /api/proxies` - Get proxies (paginated)
- `POST /api/proxies` - Add proxy
- `PUT /api/proxies/{id}` - Update proxy
- `DELETE /api/proxies` - Delete proxies
- `POST /api/proxies/test` - Test single proxy
- `POST /api/proxies/test-batch` - Test multiple proxies
- `POST /api/proxies/import` - Import proxies from text
- `GET /api/proxies/stats` - Get proxy statistics

### Profile Management
- `GET /api/profiles` - Get profiles (paginated)
- `POST /api/profiles` - Create profile
- `GET /api/profiles/{id}` - Get single profile
- `PUT /api/profiles/{id}` - Update profile
- `DELETE /api/profiles` - Delete profiles
- `POST /api/profiles/{id}/start` - Start profile
- `POST /api/profiles/{id}/stop` - Stop profile
- `POST /api/profiles/{id}/duplicate` - Duplicate profile
- `GET /api/profiles/stats` - Get profile statistics

### System Information
- `GET /api/info/plans` - Get subscription plans
- `GET /api/info/system` - Get system info and updates
- `GET /health` - Health check

### Tags and Groups
- `GET /api/tags` - Get all tags
- `GET /api/groups` - Get all groups

## API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Database

The backend uses SQLite by default with the following tables:
- `users` - User accounts
- `proxies` - Proxy configurations
- `profiles` - Browser profiles
- `tags` - Tags for organization
- `groups` - Profile groups
- Association tables for many-to-many relationships

## Frontend Integration

Update your frontend's `.env` file to point to this backend:

```env
BASE_URL=http://localhost:8000
API_PLANS_URL=http://localhost:8000/api/info/plans
API_SYSTEM_URL=http://localhost:8000/api/info/system
```

## Development

### Project Structure
```
pmlogin-back/
├── main.py              # FastAPI application
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── auth.py              # Authentication utilities
├── services/            # Business logic
│   ├── proxy_service.py # Proxy management
│   └── profile_service.py # Profile management
├── requirements.txt     # Dependencies
├── start.py            # Startup script
└── .env                # Environment variables
```

### Adding New Features

1. **Add models** in `models.py`
2. **Add schemas** in `schemas.py`
3. **Create service** in `services/`
4. **Add endpoints** in `main.py`

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Deployment

### Using systemd (Linux)

1. Create service file:
```bash
sudo nano /etc/systemd/system/pmlogin-backend.service
```

2. Add configuration:
```ini
[Unit]
Description=PM Login Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/pmlogin-back
Environment=PATH=/path/to/pmlogin-back/venv/bin
ExecStart=/path/to/pmlogin-back/venv/bin/python start.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable pmlogin-backend
sudo systemctl start pmlogin-backend
```

### Using nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Considerations

1. **Change the SECRET_KEY** in production
2. **Use HTTPS** in production
3. **Configure CORS** properly
4. **Use environment variables** for sensitive data
5. **Regular security updates**

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Change PORT in .env or kill existing process
   lsof -ti:8000 | xargs kill -9
   ```

2. **Database locked:**
   ```bash
   # Remove database file and restart
   rm pmlogin.db
   ```

3. **Import errors:**
   ```bash
   # Ensure virtual environment is activated
   pip install -r requirements.txt
   ```

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify environment configuration
3. Ensure all dependencies are installed
4. Check database permissions

## License

This project is part of the PM Login application suite.