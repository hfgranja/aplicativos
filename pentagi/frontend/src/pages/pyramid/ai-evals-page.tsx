import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from '@/components/ui/breadcrumb';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';

interface PyramidFinding {
    id: number;
    engine: string;
    pyramid_level: number;
    severity: string;
    category: string;
    title: string;
    description: string;
    neural_score?: number;
    is_resolved: boolean;
    is_accepted_risk: boolean;
    created_at: string;
}

const AI_EVAL_CATEGORIES = [
    {
        key: 'hallucination',
        label: 'Hallucination Detection',
        icon: '🧠',
        description: 'Detects factual inconsistencies between prompt context and LLM output',
        color: 'border-purple-500/30 bg-purple-500/10',
    },
    {
        key: 'prompt_injection',
        label: 'Prompt Injection',
        icon: '💉',
        description: 'Tests for OWASP LLM Top 10 prompt injection vulnerabilities',
        color: 'border-red-500/30 bg-red-500/10',
    },
    {
        key: 'rag_quality',
        label: 'RAG Quality',
        icon: '📚',
        description: 'Validates retrieval relevance and answer grounding for RAG applications',
        color: 'border-blue-500/30 bg-blue-500/10',
    },
    {
        key: 'bias_toxicity',
        label: 'Bias & Toxicity',
        icon: '⚖️',
        description: 'Detects offensive content and protected-attribute bias in LLM outputs',
        color: 'border-orange-500/30 bg-orange-500/10',
    },
];

const severityColor: Record<string, string> = {
    critical: 'text-red-400',
    high: 'text-orange-400',
    medium: 'text-yellow-400',
    low: 'text-blue-400',
    info: 'text-gray-400',
};

const AIEvalsPage = () => {
    const [findings, setFindings] = useState<PyramidFinding[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeCategory, setActiveCategory] = useState<string | null>(null);

    useEffect(() => {
        fetch('/api/v1/pyramid/findings/?engine=ai_evals')
            .then((r) => r.json())
            .then((d) => setFindings(d.data?.findings || []))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const findingsForCategory = (cat: string) =>
        findings.filter((f) => f.category?.toLowerCase().includes(cat));

    const displayFindings = activeCategory ? findingsForCategory(activeCategory) : findings;

    return (
        <div className="flex h-full flex-col">
            <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator
                    className="mr-2 h-4"
                    orientation="vertical"
                />
                <Breadcrumb>
                    <BreadcrumbList>
                        <BreadcrumbItem>
                            <Link
                                className="text-muted-foreground hover:text-foreground"
                                to="/pyramid"
                            >
                                Testing Pyramid
                            </Link>
                        </BreadcrumbItem>
                        <BreadcrumbItem>
                            <BreadcrumbPage>AI Evals</BreadcrumbPage>
                        </BreadcrumbItem>
                    </BreadcrumbList>
                </Breadcrumb>
            </header>

            <div className="flex-1 overflow-auto p-6">
                <div className="mb-6">
                    <h1 className="text-2xl font-bold">AI Evals Engine</h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        Level 11 — Tests LLM/AI agent applications for hallucination, prompt injection, RAG quality, and bias
                    </p>
                </div>

                {/* Category Cards */}
                <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {AI_EVAL_CATEGORIES.map((cat) => {
                        const count = findingsForCategory(cat.key).length;
                        const active = activeCategory === cat.key;
                        return (
                            <button
                                key={cat.key}
                                className={`rounded-xl border p-4 text-left transition-all ${cat.color} ${active ? 'ring-2 ring-offset-1' : 'hover:opacity-90'}`}
                                onClick={() => setActiveCategory(active ? null : cat.key)}
                            >
                                <div className="mb-2 text-2xl">{cat.icon}</div>
                                <div className="font-semibold">{cat.label}</div>
                                <div className="text-muted-foreground mt-1 text-xs">{cat.description}</div>
                                <div className="mt-3 text-sm font-bold">
                                    {count} {count === 1 ? 'finding' : 'findings'}
                                </div>
                            </button>
                        );
                    })}
                </div>

                {/* Findings */}
                <h2 className="mb-3 text-lg font-semibold">
                    {activeCategory
                        ? `${AI_EVAL_CATEGORIES.find((c) => c.key === activeCategory)?.label} Findings`
                        : 'All AI Eval Findings'}
                </h2>

                {loading ? (
                    <div className="text-muted-foreground py-10 text-center">Loading AI eval findings…</div>
                ) : displayFindings.length === 0 ? (
                    <div className="text-muted-foreground py-10 text-center">
                        No AI eval findings yet. Run a test plan with the <code>ai_evals</code> engine enabled.
                    </div>
                ) : (
                    <div className="space-y-2">
                        {displayFindings.map((f) => (
                            <div
                                key={f.id}
                                className="bg-card rounded-lg border p-4"
                            >
                                <div className="flex items-start justify-between">
                                    <div>
                                        <div className="mb-1 flex items-center gap-2">
                                            <span className={`text-xs font-semibold uppercase ${severityColor[f.severity] || ''}`}>
                                                {f.severity}
                                            </span>
                                            <span className="text-muted-foreground text-xs">{f.category}</span>
                                        </div>
                                        <div className="font-medium">{f.title}</div>
                                        {f.description && (
                                            <div className="text-muted-foreground mt-1 text-sm line-clamp-2">
                                                {f.description}
                                            </div>
                                        )}
                                    </div>
                                    {f.neural_score != null && (
                                        <div className="text-muted-foreground ml-4 shrink-0 text-right text-xs">
                                            <div>Neural</div>
                                            <div className="font-medium">{Math.round(f.neural_score * 100)}%</div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AIEvalsPage;
