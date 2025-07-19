# Project Structure & Organization

## Monorepo Architecture
LLMO uses a monorepo structure with separate frontend and backend applications under the `apps/` directory.

```
LLMO/
├── apps/
│   ├── frontend/          # Next.js React application
│   │   ├── app/           # App router pages & layouts
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx # Root layout with metadata
│   │   │   └── page.tsx   # Homepage component
│   │   ├── next.config.js
│   │   ├── package.json
│   │   └── tailwind.config.js
│   └── backend/           # FastAPI Python application
│       ├── services/      # Business logic services
│       │   ├── __init__.py
│       │   ├── llm_service.py      # LLM API integrations
│       │   └── web_scraper.py      # Website auditing logic
│       ├── main.py        # FastAPI app entry point
│       └── requirements.txt
├── docker-compose.yml     # Container orchestration
├── .env.example          # Environment variables template
├── package.json          # Root package.json
├── requirements.txt      # Root Python dependencies
├── PROJECT_SUMMARY.md    # Executive summary
└── README.md            # Technical documentation
```

## Code Organization Patterns

### Backend Structure
- **main.py**: FastAPI app initialization, CORS setup, route definitions
- **services/**: Business logic separated by domain
  - `llm_service.py`: OpenAI/Anthropic API interactions
  - `web_scraper.py`: Website auditing and content analysis
- **Pydantic Models**: Request/response schemas defined inline in main.py
- **Error Handling**: Try-catch blocks with descriptive error messages

### Frontend Structure  
- **App Router**: Next.js 14 app directory structure
- **Component Pattern**: Inline functional components for simple UI elements
- **Styling**: Tailwind CSS utility classes
- **Layout**: Single root layout with Inter font and metadata

### API Design Patterns
- **RESTful Endpoints**: `/api/{feature}/{action}` naming convention
- **Request Models**: Pydantic schemas for type safety
- **Response Format**: Consistent JSON structure with status indicators
- **Health Checks**: `/api/health` endpoint for monitoring

### Development Conventions
- **Environment Config**: `.env` files for API keys and settings
- **CORS**: Explicit localhost origins for development
- **Hot Reload**: Both frontend and backend support live reloading
- **Docker**: Multi-service setup with volume mounting for development

### File Naming
- **Python**: snake_case for files and functions
- **TypeScript/React**: PascalCase for components, camelCase for functions
- **Config Files**: kebab-case (docker-compose.yml, next.config.js)