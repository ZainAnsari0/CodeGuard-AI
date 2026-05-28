import { Link } from 'react-router-dom'
import { Shield, FileCode, Zap, Share2, Bug, ArrowRight, ExternalLink, Terminal, Lock } from 'lucide-react'

export function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Navbar */}
      <nav className="border-b border-border-default bg-bg-primary/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <Shield className="w-7 h-7 text-brand-400" />
            <span className="text-xl font-bold text-text-primary">CodeGuard AI</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Sign in
            </Link>
            <Link to="/register" className="btn-primary text-sm px-4 py-2">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-medium mb-6">
            <Zap className="w-3.5 h-3.5" />
            AI-Powered Security Analysis
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-text-primary mb-6 leading-tight">
            Find vulnerabilities <br className="hidden sm:block" />
            <span className="text-brand-400">before they find you</span>
          </h1>
          <p className="text-lg sm:text-xl text-text-secondary max-w-2xl mx-auto mb-10">
            CodeGuard AI scans your code for security vulnerabilities, explains them in plain English,
            and generates fix suggestions — all powered by multi-model AI analysis.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register" className="btn-primary px-8 py-3 text-base font-semibold">
              Start Scanning Free <ArrowRight className="w-4 h-4 inline ml-1" />
            </Link>
            <Link to="/demo" className="btn-secondary px-8 py-3 text-base font-semibold">
              Try Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-bg-secondary/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-text-primary mb-4">
              Comprehensive Security Analysis
            </h2>
            <p className="text-text-secondary max-w-xl mx-auto">
              From detection to remediation, CodeGuard AI covers your entire security workflow.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <FeatureCard
              icon={<Bug className="w-6 h-6" />}
              title="Vulnerability Detection"
              description="AST-based scanning with AI enrichment detects SQL injection, XSS, path traversal, hardcoded credentials, and more."
            />
            <FeatureCard
              icon={<Terminal className="w-6 h-6" />}
              title="AI Fix Suggestions"
              description="Get actionable, validated fix suggestions with code diffs. Every fix passes AST validation before it reaches you."
            />
            <FeatureCard
              icon={<FileCode className="w-6 h-6" />}
              title="Multi-Language Support"
              description="Analyze Python, JavaScript, TypeScript, Java, Go, Rust, and more. Automatic language detection from file extensions."
            />
            <FeatureCard
              icon={<Share2 className="w-6 h-6" />}
              title="Shareable Reports"
              description="Generate shareable links for your scan results. Collaborate with your team on security findings without needing accounts."
            />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-text-primary mb-4">
              How It Works
            </h2>
            <p className="text-text-secondary max-w-xl mx-auto">
              Three steps from upload to secure code.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <StepCard step={1} title="Upload Your Code" description="Drag and drop your source files or upload a ZIP archive. We support all major programming languages." />
            <StepCard step={2} title="AI Analysis" description="Our multi-model AI pipeline analyzes your code for vulnerabilities, enriches findings with explanations, and generates fix suggestions." />
            <StepCard step={3} title="Review & Fix" description="Browse findings with severity ratings, view vulnerable code with line highlighting, apply AI-suggested fixes, and re-scan to verify." />
          </div>
        </div>
      </section>

      {/* Security badges */}
      <section className="py-16 bg-bg-secondary/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div className="glass-card p-6">
              <Lock className="w-8 h-8 text-success mx-auto mb-3" />
              <h3 className="font-semibold text-text-primary mb-1">OWASP-Aligned</h3>
              <p className="text-sm text-text-secondary">Covers OWASP Top 10 vulnerability categories with CWE classifications.</p>
            </div>
            <div className="glass-card p-6">
              <Shield className="w-8 h-8 text-brand-400 mx-auto mb-3" />
              <h3 className="font-semibold text-text-primary mb-1">Validated Fixes</h3>
              <p className="text-sm text-text-secondary">Every suggested fix passes AST re-validation to ensure syntactic correctness.</p>
            </div>
            <div className="glass-card p-6">
              <Zap className="w-8 h-8 text-warning mx-auto mb-3" />
              <h3 className="font-semibold text-text-primary mb-1">Multi-Model AI</h3>
              <p className="text-sm text-text-secondary">OpenAI, Groq, and Ollama fallback chain ensures analysis always completes.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-text-primary mb-4">
              Trusted by Developers
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <TestimonialCard
              quote="CodeGuard AI caught a SQL injection vulnerability that our manual code review missed. The fix suggestion was spot-on."
              author="Sarah K."
              role="Senior Backend Engineer"
            />
            <TestimonialCard
              quote="The AI-powered explanations make security accessible to our entire team, not just security specialists."
              author="Marcus L."
              role="Engineering Manager"
            />
            <TestimonialCard
              quote="We integrated CodeGuard into our CI pipeline. The shareable reports make it easy to track remediation across sprints."
              author="Priya R."
              role="DevSecOps Lead"
            />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-brand-500/5 border-t border-brand-500/10">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-text-primary mb-4">
            Start securing your code today
          </h2>
          <p className="text-text-secondary mb-8">
            No credit card required. Upload your first project and get results in minutes.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register" className="btn-primary px-8 py-3 text-base font-semibold">
              Create Free Account <ArrowRight className="w-4 h-4 inline ml-1" />
            </Link>
            <Link to="/demo" className="btn-secondary px-8 py-3 text-base font-semibold">
              View Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border-default py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-brand-400" />
              <span className="text-sm font-semibold text-text-primary">CodeGuard AI</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-text-muted">
              <span>Automated Security Analysis</span>
              <span>&copy; {new Date().getFullYear()}</span>
            </div>
            <div className="flex items-center gap-4">
              <a href="#" className="text-text-muted hover:text-text-primary transition-colors">
                <ExternalLink className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="glass-card p-6 hover:border-brand-500/30 transition-colors">
      <div className="w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-400 mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">{title}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{description}</p>
    </div>
  )
}

function StepCard({ step, title, description }: { step: number; title: string; description: string }) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 rounded-full bg-brand-500/10 border-2 border-brand-500/30 flex items-center justify-center text-brand-400 font-bold text-lg mx-auto mb-4">
        {step}
      </div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">{title}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{description}</p>
    </div>
  )
}

function TestimonialCard({ quote, author, role }: { quote: string; author: string; role: string }) {
  return (
    <div className="glass-card p-6">
      <p className="text-text-secondary text-sm leading-relaxed mb-4 italic">"{quote}"</p>
      <div>
        <p className="text-sm font-semibold text-text-primary">{author}</p>
        <p className="text-xs text-text-muted">{role}</p>
      </div>
    </div>
  )
}