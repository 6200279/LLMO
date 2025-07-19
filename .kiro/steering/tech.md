# Technology Stack & Build System

## Frontend Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: React 18
- **Font**: Inter (Google Fonts)

## Backend Stack
- **Framework**: FastAPI
- **Language**: Python 3.9+
- **API Documentation**: Auto-generated OpenAPI/Swagger
- **HTTP Client**: Requests
- **HTML Parsing**: BeautifulSoup4
- **Data Validation**: Pydantic v2

## LLM Integration
- **OpenAI**: GPT models via official Python client
- **Anthropic**: Claude models via official Python client
- **API Management**: Environment-based key configuration

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
# Run entire stack
docker-compose up --build

# Access points:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
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

## Environment Variables
- `OPENAI_API_KEY`: Required for LLM queries
- `ANTHROPIC_API_KEY`: Required for Claude integration
- `NODE_ENV`: Frontend environment setting