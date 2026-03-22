import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';

interface TestPlan {
    id: number;
    name: string;
    mode: string;
    engines: string[];
    created_at: string;
}

interface TestRun {
    id: number;
    engine: string;
    pyramid_level: number;
    status: string;
    score: number;
    summary: string;
    execution_time_ms: number;
}

interface PyramidSummary {
    test_plan_id: number;
    total_engines: number;
    completed_runs: number;
    total_findings: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    overall_score: number;
    pyramid_coverage: number;
    engine_results: TestRun[];
    latest_decision?: {
        decision: string;
        score: number;
        summary: string;
        decided_at: string;
    };
}

const PYRAMID_LEVELS: { level: number; label: string; engine: string }[] = [
    { level: 11, label: 'AI Evals', engine: 'ai_evals' },
    { level: 10, label: 'Chaos / Resilience', engine: 'chaos' },
    { level: 9, label: 'Security / Pentest', engine: 'security' },
    { level: 8, label: 'Performance / Load', engine: 'performance' },
    { level: 7, label: 'End-to-End (E2E)', engine: 'e2e' },
    { level: 6, label: 'Differential / A-B', engine: 'differential' },
    { level: 5, label: 'API / Contract', engine: 'contract' },
    { level: 4, label: 'Integration', engine: 'integration' },
    { level: 3, label: 'Fuzzing', engine: 'fuzzing' },
    { level: 2, label: 'Property-Based', engine: 'property_based' },
    { level: 1, label: 'Mutation Testing', engine: 'mutation' },
    { level: 0, label: 'Static / SAST', engine: 'sast' },
];

const decisionColor: Record<string, string> = {
    green: 'text-green-500',
    yellow: 'text-yellow-500',
    red: 'text-red-500',
};

const statusColor: Record<string, string> = {
    completed: 'bg-green-500/20 text-green-400',
    running: 'bg-blue-500/20 text-blue-400',
    failed: 'bg-red-500/20 text-red-400',
    pending: 'bg-gray-500/20 text-gray-400',
    cancelled: 'bg-gray-500/20 text-gray-400',
};

const PyramidOverview = () => {
    const [plans, setPlans] = useState<TestPlan[]>([]);
    const [selectedPlan, setSelectedPlan] = useState<number | null>(null);
    const [summary, setSummary] = useState<PyramidSummary | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetch('/api/v1/pyramid/plans/')
            .then((r) => r.json())
            .then((d) => {
                setPlans(d.data?.plans || []);
                if (d.data?.plans?.length > 0) {
                    setSelectedPlan(d.data.plans[0].id);
                }
            })
            .catch(console.error);
    }, []);

    useEffect(() => {
        if (!selectedPlan) return;
        setLoading(true);
        fetch(`/api/v1/pyramid/plans/${selectedPlan}/summary`)
            .then((r) => r.json())
            .then((d) => setSummary(d.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [selectedPlan]);

    const getRunForEngine = (engine: string) =>
        summary?.engine_results?.find((r) => r.engine === engine);

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
                            <BreadcrumbPage>Testing Pyramid</BreadcrumbPage>
                        </BreadcrumbItem>
                    </BreadcrumbList>
                </Breadcrumb>
            </header>

            <div className="flex-1 overflow-auto p-6">
                <div className="mb-6 flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold">Universal Testing Pyramid</h1>
                        <p className="text-muted-foreground mt-1 text-sm">
                            Multi-level automated test coverage across all pyramid layers
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        {plans.length > 0 && (
                            <select
                                className="bg-background border-input rounded-md border px-3 py-1.5 text-sm"
                                onChange={(e) => setSelectedPlan(Number(e.target.value))}
                                value={selectedPlan ?? ''}
                            >
                                {plans.map((p) => (
                                    <option
                                        key={p.id}
                                        value={p.id}
                                    >
                                        {p.name}
                                    </option>
                                ))}
                            </select>
                        )}
                        <Button
                            asChild
                            size="sm"
                        >
                            <Link to="/pyramid/new">New Test Plan</Link>
                        </Button>
                    </div>
                </div>

                {/* Summary Cards */}
                {summary && (
                    <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
                        <div className="bg-card rounded-lg border p-4">
                            <div className="text-muted-foreground text-sm">Coverage</div>
                            <div className="mt-1 text-3xl font-bold">
                                {Math.round((summary.pyramid_coverage || 0) * 100)}%
                            </div>
                        </div>
                        <div className="bg-card rounded-lg border p-4">
                            <div className="text-muted-foreground text-sm">Overall Score</div>
                            <div className="mt-1 text-3xl font-bold">{summary.overall_score}</div>
                        </div>
                        <div className="bg-card rounded-lg border p-4">
                            <div className="text-muted-foreground text-sm">Findings</div>
                            <div className="mt-1 text-3xl font-bold">{summary.total_findings}</div>
                            <div className="mt-1 flex gap-2 text-xs">
                                <span className="text-red-400">C:{summary.critical_count}</span>
                                <span className="text-orange-400">H:{summary.high_count}</span>
                                <span className="text-yellow-400">M:{summary.medium_count}</span>
                                <span className="text-blue-400">L:{summary.low_count}</span>
                            </div>
                        </div>
                        <div className="bg-card rounded-lg border p-4">
                            <div className="text-muted-foreground text-sm">Release Gate</div>
                            {summary.latest_decision ? (
                                <div
                                    className={`mt-1 text-3xl font-bold uppercase ${decisionColor[summary.latest_decision.decision] || ''}`}
                                >
                                    {summary.latest_decision.decision}
                                </div>
                            ) : (
                                <div className="text-muted-foreground mt-1 text-sm">Not evaluated</div>
                            )}
                        </div>
                    </div>
                )}

                {/* Pyramid Visualization */}
                {loading ? (
                    <div className="text-muted-foreground py-20 text-center">Loading pyramid data…</div>
                ) : (
                    <div className="bg-card space-y-1 rounded-lg border p-6">
                        {PYRAMID_LEVELS.map(({ level, label, engine }) => {
                            const run = getRunForEngine(engine);
                            const width = `${Math.max(30, 100 - level * 7)}%`;

                            return (
                                <div
                                    key={engine}
                                    className="flex items-center gap-4"
                                >
                                    <div className="text-muted-foreground w-6 text-right text-xs">{level}</div>
                                    <div
                                        className="flex items-center justify-between rounded px-3 py-2 transition-colors"
                                        style={{
                                            background: run ? '#1e40af22' : '#1e253622',
                                            border: '1px solid',
                                            borderColor: run ? '#1e40af66' : '#1e253644',
                                            width,
                                            minWidth: '200px',
                                        }}
                                    >
                                        <span className="text-sm font-medium">{label}</span>
                                        <div className="flex items-center gap-2">
                                            {run ? (
                                                <>
                                                    <span
                                                        className={`rounded px-1.5 py-0.5 text-xs ${statusColor[run.status] || ''}`}
                                                    >
                                                        {run.status}
                                                    </span>
                                                    <span className="text-muted-foreground text-xs">
                                                        Score: {run.score}
                                                    </span>
                                                </>
                                            ) : (
                                                <span className="text-muted-foreground text-xs">not run</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Findings Link */}
                {summary && summary.total_findings > 0 && (
                    <div className="mt-6 text-center">
                        <Button
                            asChild
                            variant="outline"
                        >
                            <Link to="/findings">View All Findings ({summary.total_findings})</Link>
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PyramidOverview;
