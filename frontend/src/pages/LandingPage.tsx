import { Link } from 'react-router-dom'
import { Shield, FileCode, Zap, Share2, Bug, ArrowRight, Terminal, Lock, Eye, Code, Sparkles, ChevronRight } from 'lucide-react'

export function LandingPage() {
  return (
    <div className="min-h-screen bg-surface">
      {/* ─── Navbar ─── */}
      <nav className="border-b border-outline-variant/30 bg-surface-container/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-[1440px] mx-auto px-6 flex items-center justify-between h-16">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center shadow-glow-cyan-sm">
              <Shield className="w-4.5 h-4.5 text-white" />
            </div>
            <span className="text-lg font-bold text-on-surface tracking-tight">
              CodeGuard <span className="text-label-sm text-brand-400 tracking-widest uppercase align-super text-[10px]">AI</span>
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-on-surface-variant hover:text-on-surface transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm text-on-surface-variant hover:text-on-surface transition-colors">How It Works</a>
            <a href="#" className="text-sm text-on-surface-variant hover:text-on-surface transition-colors">Docs</a>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="text-sm font-medium text-on-surface-variant hover:text-on-surface transition-colors px-4 py-2"
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className="text-sm font-semibold px-5 py-2.5 rounded-lg btn-gradient flex items-center gap-2"
            >
              Get Started <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ─── Hero Section ─── */}
      <section className="relative overflow-hidden">
        {/* Background decorative elements */}
        <div className="absolute inset-0 bg-grid-pattern opacity-40" />
        <div className="absolute top-1/4 left-1/6 w-80 h-80 rounded-full bg-brand-500/8 blur-[100px]" />
        <div className="absolute bottom-1/3 right-1/6 w-96 h-96 rounded-full bg-accent-500/6 blur-[120px]" />

        <div className="relative max-w-[1440px] mx-auto px-6 pt-20 pb-24">
          <div className="max-w-3xl mx-auto text-center mb-16">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 mb-8 animate-fade-in">
              <Sparkles className="w-3.5 h-3.5 text-brand-400" />
              <span className="text-label-sm text-brand-400 font-medium">AI-Powered Security Analysis</span>
            </div>

            {/* Animated gradient heading */}
            <h1 className="text-display-xl md:text-[48px] md:leading-[56px] font-bold text-on-surface mb-6 leading-tight" style={{ animation: 'fade-in 0.6s ease-out' }}>
              Find vulnerabilities<br />
              <span className="gradient-text" style={{ backgroundSize: '200% auto', animation: 'gradient-move 3s ease infinite' }}>
                before they find you
              </span>
            </h1>

            <p className="text-body-lg text-on-surface-variant max-w-2xl mx-auto mb-10 leading-relaxed">
              CodeGuard AI - Updated scans your code for security vulnerabilities, explains them in plain English,
              and generates fix suggestions — all powered by multi-model AI analysis.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/register"
                className="px-8 py-3.5 rounded-lg btn-gradient text-body-md font-semibold flex items-center gap-2 shadow-glow-cyan"
              >
                Start Scanning Free <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/demo"
                className="px-8 py-3.5 rounded-lg btn-secondary text-body-md font-medium flex items-center gap-2"
              >
                <Eye className="w-4 h-4" /> Try Demo
              </Link>
            </div>
          </div>

          {/* Code editor mockup */}
          <div className="max-w-4xl mx-auto" style={{ animation: 'slide-up 0.6s ease-out 0.2s both' }}>
            <div className="glass-panel rounded-xl overflow-hidden shadow-card-hover">
              {/* Editor chrome */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-outline-variant/30 bg-surface-lowest/50">
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-severity-critical/60" />
                  <div className="w-3 h-3 rounded-full bg-severity-medium/60" />
                  <div className="w-3 h-3 rounded-full bg-success/60" />
                </div>
                <div className="flex-1 flex items-center justify-center gap-4">
                  <span className="text-label-sm text-on-surface-variant/60 px-3 py-1 bg-surface-high rounded">app.py</span>
                  <span className="text-label-sm text-on-surface-variant/40 px-3 py-1">utils.py</span>
                </div>
              </div>
              {/* Code content */}
              <div className="p-5 font-mono text-[13px] leading-relaxed bg-surface-lowest">
                <div className="flex">
                  <span className="text-on-surface-variant/30 select-none w-8 text-right mr-4">1</span>
                  <span><span className="code-keyword">from</span> flask <span className="code-keyword">import</span> Flask, request</span>
                </div>
                <div className="flex">
                  <span className="text-on-surface-variant/30 select-none w-8 text-right mr-4">2</span>
                  <span><span className="code-keyword">from</span> database <span className="code-keyword">import</span> <span className="code-function">execute_query</span></span>
                </div>
                <div className="flex code-vulnerable">
                  <span className="text-on-surface-variant/30 select-none w-8 text-right mr-4">3</span>
                  <span><span className="code-keyword">def</span> <span className="code-function">get_user</span>(user_id):</span>
                </div>
                <div className="flex code-vulnerable">
                  <span className="text-on-surface-variant/30 select-none w-8 text-right mr-4">4</span>
                  <span className="ml-4"><span className="code-keyword">query</span> = <span className="code-string">f"SELECT * FROM users WHERE id = '</span>{<span className="text-brand-400">user_id</span>}<span className="code-string">'"</span></span>
                </div>
                <div className="flex code-vulnerable">
                  <span className="text-on-surface-variant/30 select-none w-8 text-right mr-4">5</span>
                  <span className="ml-4"><span className="code-keyword">return</span> <span className="code-function">execute_query</span>(<span className="code-keyword">query</span>)</span>
                </div>
                <div className="flex">
                  <span className="text-on-surface-variant/30 select-none w-8 text-right mr-4">6</span>
                  <span className="text-on-surface-variant/40"></span>
                </div>
                {/* Finding callout */}
                <div className="mt-3 flex items-start gap-3 p-3 rounded-lg bg-severity-critical-bg border border-severity-critical/20">
                  <Bug className="w-4 h-4 text-severity-critical shrink-0 mt-0.5" />
                  <div>
                    <p className="text-label-sm font-medium text-severity-critical">SQL Injection — CWE-89</p>
                    <p className="text-xs text-on-surface-variant mt-0.5">User input directly interpolated into SQL query. Use parameterized queries instead.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Features Bento Grid ─── */}
      <section id="features" className="relative py-24">
        <div className="absolute top-0 left-1/3 w-64 h-64 rounded-full bg-accent-500/5 blur-[100px]" />
        <div className="max-w-[1440px] mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-display-lg font-bold text-on-surface mb-4">
              Comprehensive Security Analysis
            </h2>
            <p className="text-body-lg text-on-surface-variant max-w-xl mx-auto">
              From detection to remediation, CodeGuard AI - Updated covers your entire security workflow.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <FeatureCard
              icon={<Bug className="w-6 h-6" />}
              title="Vulnerability Detection"
              description="AST-based scanning with AI enrichment detects SQL injection, XSS, path traversal, hardcoded credentials, and more."
              gradient="from-severity-critical to-severity-high"
            />
            <FeatureCard
              icon={<Terminal className="w-6 h-6" />}
              title="AI Fix Suggestions"
              description="Get actionable, validated fix suggestions with code diffs. Every fix passes AST validation before it reaches you."
              gradient="from-brand-400 to-accent-500"
            />
            <FeatureCard
              icon={<FileCode className="w-6 h-6" />}
              title="Multi-Language Support"
              description="Analyze Python, JavaScript, TypeScript, Java, Go, Rust, and more. Automatic language detection from file extensions."
              gradient="from-success to-brand-500"
            />
            <FeatureCard
              icon={<Share2 className="w-6 h-6" />}
              title="Shareable Reports"
              description="Generate shareable links for your scan results. Collaborate with your team on security findings without needing accounts."
              gradient="from-accent-400 to-accent-600"
            />
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section id="how-it-works" className="py-24 bg-surface-container/30">
        <div className="max-w-[1440px] mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-display-lg font-bold text-on-surface mb-4">
              How It Works
            </h2>
            <p className="text-body-lg text-on-surface-variant max-w-xl mx-auto">
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

      {/* ─── Security Badges ─── */}
      <section className="py-20">
        <div className="max-w-[1440px] mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div className="glass-card p-8 hover:border-primary/30 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center mx-auto mb-4">
                <Lock className="w-6 h-6 text-success" />
              </div>
              <h3 className="text-headline-sm font-semibold text-on-surface mb-2">OWASP-Aligned</h3>
              <p className="text-body-sm text-on-surface-variant leading-relaxed">Covers OWASP Top 10 vulnerability categories with CWE classifications.</p>
            </div>
            <div className="glass-card p-8 hover:border-primary/30 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-brand-500/10 flex items-center justify-center mx-auto mb-4">
                <Shield className="w-6 h-6 text-brand-400" />
              </div>
              <h3 className="text-headline-sm font-semibold text-on-surface mb-2">Validated Fixes</h3>
              <p className="text-body-sm text-on-surface-variant leading-relaxed">Every suggested fix passes AST re-validation to ensure syntactic correctness.</p>
            </div>
            <div className="glass-card p-8 hover:border-primary/30 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-severity-medium/10 flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-severity-medium" />
              </div>
              <h3 className="text-headline-sm font-semibold text-on-surface mb-2">Multi-Model AI</h3>
              <p className="text-body-sm text-on-surface-variant leading-relaxed">OpenAI, Groq, and Ollama fallback chain ensures analysis always completes.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Final CTA ─── */}
      <section className="py-24 relative">
        <div className="absolute inset-0 bg-grid-pattern opacity-30" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-brand-500/6 blur-[120px]" />
        <div className="max-w-3xl mx-auto px-6 text-center relative z-10">
          <div className="glass-panel p-12 rounded-xl">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center mx-auto mb-6 shadow-glow-cyan shield-logo">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-display-lg font-bold text-on-surface mb-4">
              Start securing your code today
            </h2>
            <p className="text-body-lg text-on-surface-variant mb-8">
              No credit card required. Upload your first project and get results in minutes.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/register" className="px-8 py-3.5 rounded-lg btn-gradient font-semibold flex items-center gap-2 shadow-glow-cyan">
                Create Free Account <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/demo" className="px-8 py-3.5 rounded-lg btn-secondary font-medium flex items-center gap-2">
                <Eye className="w-4 h-4" /> View Demo
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-outline-variant/30 py-8">
        <div className="max-w-[1440px] mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-md bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center">
                <Shield className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="text-sm font-semibold text-on-surface">CodeGuard AI - Updated</span>
            </div>
            <div className="flex items-center gap-6 text-label-sm text-on-surface-variant/60">
              <span>Automated Security Analysis</span>
              <span>&copy; {new Date().getFullYear()}</span>
            </div>
            <div className="flex items-center gap-4">
              <a href="#" className="text-on-surface-variant/60 hover:text-on-surface transition-colors text-label-sm">Privacy</a>
              <a href="#" className="text-on-surface-variant/60 hover:text-on-surface transition-colors text-label-sm">Terms</a>
              <a href="#" className="text-on-surface-variant/60 hover:text-on-surface transition-colors text-label-sm">Docs</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description, gradient }: { icon: React.ReactNode; title: string; description: string; gradient: string }) {
  return (
    <div className="glass-card-hover p-6 group">
      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center mb-4 text-white
        group-hover:shadow-glow-cyan transition-shadow duration-300`}>
        {icon}
      </div>
      <h3 className="text-headline-sm font-semibold text-on-surface mb-2">{title}</h3>
      <p className="text-body-sm text-on-surface-variant leading-relaxed">{description}</p>
    </div>
  )
}

function StepCard({ step, title, description }: { step: number; title: string; description: string }) {
  return (
    <div className="glass-card p-8 text-center group hover:border-primary/30 transition-all duration-300">
      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center text-white font-bold text-lg mx-auto mb-4
        group-hover:shadow-glow-cyan transition-shadow duration-300">
        {step}
      </div>
      <h3 className="text-headline-sm font-semibold text-on-surface mb-2">{title}</h3>
      <p className="text-body-sm text-on-surface-variant leading-relaxed">{description}</p>
    </div>
  )
}