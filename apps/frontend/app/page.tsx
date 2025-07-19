export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            LLMO
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            LLM Optimization Engine
          </p>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Measure and improve your brand's visibility and suggestability 
            within Large Language Models like ChatGPT, Claude, and Perplexity.
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <FeatureCard 
            title="LLM Visibility Scanner"
            description="Check if your brand appears in LLM responses and how frequently"
          />
          <FeatureCard 
            title="Prompt Simulation Engine"
            description="Test common prompts to see if your company is mentioned"
          />
          <FeatureCard 
            title="Visibility Audit"
            description="Analyze your website for LLM-friendly content and structure"
          />
          <FeatureCard 
            title="Suggestability Optimizer"
            description="Generate optimized content and schema for better LLM visibility"
          />
          <FeatureCard 
            title="Competitor Analysis"
            description="See why competitors are being suggested more often"
          />
        </div>
      </div>
    </main>
  )
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <h3 className="text-xl font-semibold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}