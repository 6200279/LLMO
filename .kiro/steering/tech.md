# Technology Stack & Build System

## Frontend Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: React 18
- **Font**: Inter (Google Fonts)

## Backend Stack
- **Framework**: FastAPI for high-performance API
- **Language**: Python 3.9+
- **Database**: Supabase (PostgreSQL with real-time features)
- **Authentication**: Supabase Auth with JWT tokens
- **Storage**: Supabase Storage for file uploads
- **Real-time**: Supabase Realtime for live updates
- **API Documentation**: Auto-generated OpenAPI/Swagger
- **HTTP Client**: Requests
- **HTML Parsing**: BeautifulSoup4
- **Data Validation**: Pydantic v2

## LLM Integration
- **OpenAI**: GPT-3.5-turbo, GPT-4 via official Python client
- **Anthropic**: Claude 3, Claude 4 via official Python client
- **Future**: Perplexity API, Google Bard integration
- **API Management**: Environment-based key rotation, rate limiting
- **Cost Optimization**: Response caching, batch processing

## Development Environment
- **Containerization**: Docker & Docker Compose
- **CORS**: Configured for localhost:3000 ↔ localhost:8000
- **Hot Reload**: Enabled for both frontend and backend

## Common Commands

### Development Setup
```bash
# Clone and setup
git clone <repo-url>
cd LLMO
cp .env.example .env

# Frontend setup
cd apps/frontend
npm install
npm run dev  # Runs on localhost:3000

# Backend setup  
cd apps/backend
pip install -r requirements.txt
python main.py  # Runs on localhost:8000
```

### Docker Development
```bash
# Run entire stack (no database needed - using Supabase cloud)
docker-compose up --build

# Access points:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Supabase Dashboard: https://app.supabase.com
```

### Supabase Setup
```bash
# Install Supabase CLI
npm install -g supabase

# Initialize Supabase project
supabase init

# Start local Supabase (optional for development)
supabase start

# Deploy migrations to Supabase
supabase db push
```

### Production Build
```bash
# Frontend build
cd apps/frontend
npm run build
npm start

# Backend production
cd apps/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Infrastructure
- **Containerization**: Docker with Docker Compose
- **Deployment**: AWS ECS or Kubernetes ready
- **Monitoring**: CloudWatch, Sentry for error tracking
- **Security**: HTTPS, API rate limiting, input validation
- **Performance**: 99.5% uptime target, <2s API response times

## Environment Variables
- `OPENAI_API_KEY`: Required for LLM queries
- `ANTHROPIC_API_KEY`: Required for Claude integration
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_KEY`: Supabase service role key (backend only)
- `NODE_ENV`: Frontend environment setting

## Supabase Advantages

### Built-in Features
- **Authentication**: Complete auth system with social logins, email verification
- **Real-time**: WebSocket connections for live updates and progress tracking
- **Row Level Security**: Database-level security policies for data access control
- **Auto-generated APIs**: REST and GraphQL APIs generated from database schema
- **Storage**: File upload and management with CDN
- **Edge Functions**: Serverless functions for background processing

### Development Benefits
- **Rapid Development**: Pre-built authentication and database management
- **Type Safety**: Auto-generated TypeScript types from database schema
- **Local Development**: Full local Supabase stack for development
- **Migration Management**: Built-in database migration system
- **Monitoring**: Built-in analytics and performance monitoring
- **Scaling**: Automatic scaling and performance optimization

### Cost Optimization
- **No Infrastructure Management**: Fully managed backend service
- **Pay-as-you-scale**: Usage-based pricing model
- **Built-in Caching**: Automatic query optimization and caching
- **CDN Integration**: Global content delivery for static assets