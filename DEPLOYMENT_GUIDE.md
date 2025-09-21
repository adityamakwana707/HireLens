# HireLens Deployment Guide

## Dual Database Strategy Implementation

This guide explains how HireLens uses a smart dual database strategy to solve PostgreSQL dependency issues on Streamlit Cloud while maintaining full functionality.

## 🎯 Problem Solved

### Before (Issues):
- ❌ `psycopg2-binary` fails to install on Streamlit Cloud
- ❌ Requires system-level PostgreSQL dependencies
- ❌ Causes deployment failures
- ❌ Environment differences between local and cloud

### After (Solution):
- ✅ Smart dependency management
- ✅ Automatic environment detection
- ✅ Seamless deployment to Streamlit Cloud
- ✅ Same functionality in all environments
- ✅ Easy local development with PostgreSQL

## 🏗️ Architecture

### Environment Detection
The system automatically detects the environment:

```python
def detect_environment():
    if os.getenv("STREAMLIT_CLOUD"):
        return "streamlit_cloud"
    elif os.getenv("DYNO"):  # Heroku
        return "heroku"
    elif os.getenv("RAILWAY_ENVIRONMENT"):  # Railway
        return "railway"
    elif os.getenv("DEVELOPMENT") == "true":
        return "development"
    else:
        return "production"
```

### Database Strategy
- **Development**: PostgreSQL (if available) or SQLite
- **Streamlit Cloud**: SQLite (optimized for cloud)
- **Production**: PostgreSQL (preferred) or SQLite (fallback)

## 🚀 Deployment Options

### 1. Streamlit Cloud (Recommended)

#### Prerequisites:
- GitHub repository with your code
- Streamlit Cloud account

#### Steps:
1. **Push your code to GitHub**
2. **Connect to Streamlit Cloud**
3. **Set environment variables** (if needed):
   ```
   OPENAI_API_KEY=your_openai_key
   SECRET_KEY=your_secret_key
   ```
4. **Deploy** - The system will automatically:
   - Detect Streamlit Cloud environment
   - Use SQLite database
   - Skip PostgreSQL dependencies
   - Optimize for cloud performance

#### Streamlit Cloud Configuration:
The system automatically detects `STREAMLIT_CLOUD` environment variable and:
- Uses SQLite database (`hirelens_cloud.db`)
- Applies cloud-specific optimizations
- Handles file uploads in temp directory
- Optimizes memory usage

### 2. Local Development

#### With PostgreSQL (Recommended):
```bash
# Set environment variables
export DEVELOPMENT=true
export DATABASE_URL="postgresql://user:password@localhost:5432/hirelens"

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m backend.db.init_db

# Run the application
streamlit run frontend/streamlit_app.py
```

#### With SQLite (Fallback):
```bash
# Set environment variables
export DEVELOPMENT=true

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m backend.db.init_db

# Run the application
streamlit run frontend/streamlit_app.py
```

### 3. Production Deployment

#### With PostgreSQL:
```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@host:5432/hirelens"
export SECRET_KEY="your-secret-key"
export OPENAI_API_KEY="your-openai-key"

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m backend.db.init_db

# Run with production server
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

#### With SQLite (Fallback):
```bash
# Set environment variables
export SECRET_KEY="your-secret-key"
export OPENAI_API_KEY="your-openai-key"

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m backend.db.init_db

# Run with production server
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | Database connection string | No | Auto-detected |
| `DEVELOPMENT` | Development mode flag | No | `false` |
| `STREAMLIT_CLOUD` | Streamlit Cloud detection | Auto | - |
| `SECRET_KEY` | Application secret key | Production | Generated |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |

### Smart Dependencies

The `requirements.txt` uses conditional dependencies:

```txt
# PostgreSQL - Only for non-cloud environments
psycopg2-binary==2.9.9; platform_system != "Linux" and not (os.environ.get("STREAMLIT_CLOUD") or os.environ.get("DYNO"))

# SQLite - Always available
aiosqlite==0.19.0
```

## 📊 Database Migration

### From SQLite to PostgreSQL:
```bash
# Set up PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/hirelens"

# Run migration
python -m backend.db.init_db migrate
```

### Database Reset:
```bash
# Reset database (WARNING: Deletes all data)
python -m backend.db.init_db reset
```

## 🐛 Troubleshooting

### Common Issues:

1. **PostgreSQL Connection Failed**
   - Solution: System automatically falls back to SQLite
   - Check: Database URL format and credentials

2. **Streamlit Cloud Deployment Fails**
   - Solution: Ensure no hardcoded PostgreSQL dependencies
   - Check: Environment variables are set correctly

3. **File Upload Issues on Cloud**
   - Solution: System uses temp directory for cloud
   - Check: File size limits (5MB for Streamlit Cloud)

4. **Database Not Initialized**
   - Solution: Run `python -m backend.db.init_db`
   - Check: Database permissions and connection

### Debug Mode:
```bash
# Enable debug logging
export DEBUG=true
python -m backend.db.init_db
```

## 📈 Performance Optimizations

### Streamlit Cloud:
- SQLite with connection pooling
- Optimized file handling
- Reduced memory footprint
- Efficient query patterns

### Production:
- PostgreSQL with connection pooling
- Database indexing
- Query optimization
- Caching strategies

## 🔒 Security Considerations

- Environment-specific secret keys
- Database connection encryption
- File upload validation
- API rate limiting
- Input sanitization

## 📝 Monitoring

### Health Checks:
- Database connection status
- Environment detection
- Dependency availability
- Performance metrics

### Logging:
- Environment information
- Database type and status
- Error tracking
- Performance monitoring

## 🎉 Benefits

✅ **No functionality loss** - Same features everywhere  
✅ **Successful deployment** - Works on Streamlit Cloud  
✅ **Easy development** - PostgreSQL for local development  
✅ **Reliable production** - Automatic fallback strategies  
✅ **Smart dependencies** - Only install what's needed  
✅ **Environment awareness** - Automatic configuration  

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review environment variables
3. Check database connection
4. Verify dependency installation

The dual database strategy ensures HireLens works seamlessly across all environments while maintaining full functionality and performance.
