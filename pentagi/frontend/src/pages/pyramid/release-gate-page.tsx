import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';

interface ReleaseDecision {
    id: number;
    test_plan_id: number;
    decision: 'green' | 'yellow' | 'red';
    score: number;
    summary: string;
    blocking_findings: number[];
    decided_at: string;
}

interface TestPlan {
    id: number;
    name: string;
    mode: string;
}

const decisionConfig: Record<
    string,
    { label: string; color: string; bg: string; icon: string }
> = {
    green: {
        label: 'RELEASE APPROVED',
        color: 'text-green-400',
        bg: 'bg-green-500/10 border-green-500/30',
        icon: '✓',
    },
    yellow: {
        label: 'RELEASE WITH CAUTION',
        color: 'text-yellow-400',
        bg: 'bg-yellow-500/10 border-yellow-500/30',
        icon: '⚠',
    },
    red: {
        label: 'RELEASE BLOCKED',
        color: 'text-red-400',
        bg: 'bg-red-500/10 border-red-500/30',
        icon: '✕',
    },
};

const ReleaseGatePage = () => {
    const [plans, setPlans] = useState<TestPlan[]>([]);
    const [selectedPlan, setSelectedPlan] = useState<number | null>(null);
    const [decisions, setDecisions] = useState<ReleaseDecision[]>([]);
    const [loading, setLoading] = useState(false);
    const [evaluating, setEvaluating] = useState(false);

    useEffect(() => {
        fetch('/api/v1/pyramid/plans/')
            .then((r) => r.json())
            .then((d) => {
                const p = d.data?.plans || [];
                setPlans(p);
                if (p.length > 0) setSelectedPlan(p[0].id);
            })
            .catch(console.error);
    }, []);

    useEffect(() => {
        if (!selectedPlan) return;
        setLoading(true);
        fetch(`/api/v1/pyramid/plans/${selectedPlan}/decisions`)
            .then((r) => r.json())
            .then((d) => setDecisions(d.data?.decisions || []))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [selectedPlan]);

    const handleEvaluate = async () => {
        if (!selectedPlan) return;
        setEvaluating(true);
        try {
            const r = await fetch(`/api/v1/pyramid/plans/${selectedPlan}/evaluate`, { method: 'POST' });
            const d = await r.json();
            if (d.data) {
                setDecisions((prev) => [d.data, ...prev]);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setEvaluating(false);
        }
    };

    const latest = decisions[0];

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
                            <BreadcrumbPage>Release Gate</BreadcrumbPage>
                        </BreadcrumbItem>
                    </BreadcrumbList>
                </Breadcrumb>
            </header>

            <div className="flex-1 overflow-auto p-6">
                <div className="mb-6 flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold">Release Gate</h1>
                        <p className="text-muted-foreground mt-1 text-sm">
                            Automated go/no-go decisions based on configurable policies
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
                            disabled={!selectedPlan || evaluating}
                            onClick={handleEvaluate}
                            size="sm"
                        >
                            {evaluating ? 'Evaluating…' : 'Evaluate Release Gate'}
                        </Button>
                    </div>
                </div>

                {/* Latest Decision */}
                {latest && (() => {
                    const cfg = decisionConfig[latest.decision];
                    return (
                        <div className={`mb-6 rounded-xl border p-6 ${cfg.bg}`}>
                            <div className={`text-4xl font-black ${cfg.color}`}>
                                {cfg.icon} {cfg.label}
                            </div>
                            <div className="text-muted-foreground mt-2 text-sm">{latest.summary}</div>
                            <div className="mt-3 flex gap-6 text-sm">
                                <div>
                                    <span className="text-muted-foreground">Score: </span>
                                    <span className="font-medium">{latest.score}/100</span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground">Blocking findings: </span>
                                    <span className="font-medium">{latest.blocking_findings?.length || 0}</span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground">Evaluated: </span>
                                    <span className="font-medium">
                                        {new Date(latest.decided_at).toLocaleString()}
                                    </span>
                                </div>
                            </div>
                        </div>
                    );
                })()}

                {/* History */}
                <h2 className="mb-3 text-lg font-semibold">Decision History</h2>
                {loading ? (
                    <div className="text-muted-foreground py-10 text-center">Loading…</div>
                ) : decisions.length === 0 ? (
                    <div className="text-muted-foreground py-10 text-center">
                        No release decisions yet. Click "Evaluate Release Gate" to run an evaluation.
                    </div>
                ) : (
                    <div className="space-y-2">
                        {decisions.map((d) => {
                            const cfg = decisionConfig[d.decision];
                            return (
                                <div
                                    key={d.id}
                                    className="bg-card flex items-center justify-between rounded-lg border p-4"
                                >
                                    <div className="flex items-center gap-3">
                                        <span className={`text-xl font-bold ${cfg.color}`}>{cfg.icon}</span>
                                        <div>
                                            <div className={`text-sm font-semibold ${cfg.color}`}>
                                                {cfg.label}
                                            </div>
                                            <div className="text-muted-foreground text-xs">{d.summary}</div>
                                        </div>
                                    </div>
                                    <div className="text-muted-foreground text-xs">
                                        {new Date(d.decided_at).toLocaleString()}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReleaseGatePage;
