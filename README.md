# LLMO - LLM Optimization Engine

A web-based platform that helps startups, brands, and product teams measure and improve their visibility and suggestability within Large Language Models (LLMs) like ChatGPT, Claude, and Perplexity.

## 🎯 Goals & Objectives

- Enable brands to understand if LLMs are recommending them
- Simulate prompt-based mention discovery
- Audit web visibility for LLM-indexable content
- Provide actionable steps and content to increase visibility
- Offer structured data, prompt phrasing, and tool directory guidance

## 🗂 Key Features

### 1. LLM Visibility Scanner
- **Input**: Brand name, domain, product keywords
- **Output**: Scorecard showing whether the brand is mentioned in LLM answers, frequency, and competitor comparison

### 2. Prompt Simulation Engine
- Test 10–20 commonly asked prompts (e.g., "Best X tools", "How do I Y?")
- Return LLM answers highlighting if your company appears

### 3. Visibility Audit
- Crawl websites and check for Schema.org structured data
- Analyze LLM-friendly anchor phrases
- Check presence in known open LLM training sites
- Generate visibility checklist and score (0–100)

### 4. Suggestability Optimizer
- Generate JSON-LD schema
- Create optimized meta descriptions
- Provide LLM-friendly boilerplate for landing pages
- Suggest questions/answers for FAQ inclusion

### 5. Competitor Analysis
- Enter competitor name to see why they're suggested more
- Reverse engineer their mention landscape

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- OpenAI API key

### Installation

1. Clone the repository
```bash
git clone <your-repo-url>
cd LLMO
```

2. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Install frontend dependencies
```bash
cd apps/frontend
npm install
```

4. Install backend dependencies
```bash
cd ../backend
pip install -r requirements.txt
```

### Running the Application

#### Development Mode

**Frontend** (Terminal 1):
```bash
cd apps/frontend
npm run dev
```

**Backend** (Terminal 2):
```bash
cd apps/backend
python main.py
```

#### Using Docker Compose
```bash
docker-compose up --build
```

### Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
LLMO/
├── apps/
│   ├── frontend/          # Next.js React application
│   │   ├── app/           # App router pages
│   │   ├── components/    # Reusable components
│   │   └── package.json
│   └── backend/           # FastAPI Python application
│       ├── services/      # Business logic services
│       ├── main.py        # FastAPI app entry point
│       └── requirements.txt
├── docker-compose.yml     # Container orchestration
├── .env.example          # Environment variables template
└── README.md
```

## 🛠 Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.9+, Pydantic
- **LLM Integration**: OpenAI GPT, Anthropic Claude
- **Web Scraping**: BeautifulSoup4, Requests
- **Deployment**: Docker, Docker Compose

## 📝 API Endpoints

- `GET /api/health` - Health check
- `POST /api/scan/visibility` - LLM Visibility Scanner
- `POST /api/simulate/prompts` - Prompt Simulation Engine
- `POST /api/audit/visibility` - Website Visibility Audit

## 🔧 Development

The project is set up with hot reloading for both frontend and backend development. Make changes to the code and see them reflected immediately.

## 📄 License

[Your License Here]