import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';

interface FixProposal {
    explanation: string;
    before_code: string;
    after_code: string;
    diff: string;
    rationale: string;
    confidence: number;
    generated_by: string;
    generated_at: string;
}

interface PyramidFinding {
    id: number;
    engine: string;
    pyramid_level: number;
    severity: string;
    category: string;
    title: string;
    description: string;
    cwe_id?: string;
    file_path?: string;
    line_number?: number;
    neural_score?: number;
    fix_proposal?: string | FixProposal;
    is_resolved: boolean;
    is_accepted_risk: boolean;
    created_at: string;
}

const severityColor: Record<string, string> = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    info: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

const SEVERITIES = ['critical', 'high', 'medium', 'low', 'info'];

const FindingsPage = () => {
    const [findings, setFindings] = useState<PyramidFinding[]>([]);
    const [loading, setLoading] = useState(true);
    const [severityFilter, setSeverityFilter] = useState('');
    const [search, setSearch] = useState('');
    const [showResolved, setShowResolved] = useState(false);
    const [patchLoading, setPatchLoading] = useState<number | null>(null);
    const [fixLoading, setFixLoading] = useState<number | null>(null);
    const [expandedFix, setExpandedFix] = useState<number | null>(null);
    const [acceptNote, setAcceptNote] = useState('');
    const [acceptTarget, setAcceptTarget] = useState<number | null>(null);

    const fetchFindings = () => {
        setLoading(true);
        const params = new URLSearchParams();
        if (severityFilter) params.set('severity', severityFilter);
        fetch(`/api/v1/pyramid/findings/?${params}`)
            .then((r) => r.json())
            .then((d) => setFindings(d.data?.findings || []))
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchFindings();
    }, [severityFilter]);

    const handleResolve = async (id: number) => {
        setPatchLoading(id);
        try {
            await fetch(`/api/v1/pyramid/findings/${id}`, {
                body: JSON.stringify({ action: 'resolve' }),
                headers: { 'Content-Type': 'application/json' },
                method: 'PATCH',
            });
            fetchFindings();
        } catch (e) {
            console.error(e);
        } finally {
            setPatchLoading(null);
        }
    };

    const handleAcceptRisk = async (id: number) => {
        setPatchLoading(id);
        try {
            await fetch(`/api/v1/pyramid/findings/${id}`, {
                body: JSON.stringify({ action: 'accept_risk', acceptance_note: acceptNote || 'Risk accepted.' }),
                headers: { 'Content-Type': 'application/json' },
                method: 'PATCH',
            });
            setAcceptTarget(null);
            setAcceptNote('');
            fetchFindings();
        } catch (e) {
            console.error(e);
        } finally {
            setPatchLoading(null);
        }
    };

    const handleGenerateFix = async (id: number) => {
        setFixLoading(id);
        try {
            const r = await fetch(`/api/v1/pyramid/findings/${id}/generate-fix`, { method: 'POST' });
            const d = await r.json();
            if (d.data) {
                setFindings((prev) => prev.map((f) => (f.id === id ? d.data : f)));
                setExpandedFix(id);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setFixLoading(null);
        }
    };

    const parseFixProposal = (f: PyramidFinding): FixProposal | null => {
        if (!f.fix_proposal) return null;
        if (typeof f.fix_proposal === 'object') return f.fix_proposal as FixProposal;
        try {
            return JSON.parse(f.fix_proposal as string) as FixProposal;
        } catch {
            return null;
        }
    };

    const filtered = findings.filter((f) => {
        if (!showResolved && (f.is_resolved || f.is_accepted_risk)) return false;
        if (search) {
            const s = search.toLowerCase();
            return f.title.toLowerCase().includes(s) || f.category.toLowerCase().includes(s);
        }
        return true;
    });

    const countBySeverity = (sev: string) => findings.filter((f) => f.severity === sev && !f.is_resolved).length;

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
                            <BreadcrumbPage>Findings</BreadcrumbPage>
                        </BreadcrumbItem>
                    </BreadcrumbList>
                </Breadcrumb>
            </header>

            <div className="flex-1 overflow-auto p-6">
                <div className="mb-6">
                    <h1 className="text-2xl font-bold">Security Findings</h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        All findings detected across testing pyramid engines
                    </p>
                </div>

                {/* Severity Summary */}
                <div className="mb-6 flex flex-wrap gap-3">
                    {SEVERITIES.map((sev) => (
                        <button
                            key={sev}
                            className={`rounded-lg border px-4 py-2 text-sm font-medium transition-all ${
                                severityFilter === sev ? 'ring-2 ring-offset-1' : 'opacity-80 hover:opacity-100'
                            } ${severityColor[sev]}`}
                            onClick={() => setSeverityFilter(severityFilter === sev ? '' : sev)}
                        >
                            {sev.toUpperCase()} ({countBySeverity(sev)})
                        </button>
                    ))}
                </div>

                {/* Filters */}
                <div className="mb-4 flex items-center gap-3">
                    <input
                        className="bg-background border-input flex-1 rounded-md border px-3 py-1.5 text-sm"
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search findings..."
                        value={search}
                    />
                    <label className="flex cursor-pointer items-center gap-2 text-sm">
                        <input
                            checked={showResolved}
                            className="rounded"
                            onChange={(e) => setShowResolved(e.target.checked)}
                            type="checkbox"
                        />
                        Show resolved
                    </label>
                </div>

                {/* Findings Table */}
                {loading ? (
                    <div className="text-muted-foreground py-20 text-center">Loading findings…</div>
                ) : filtered.length === 0 ? (
                    <div className="text-muted-foreground py-20 text-center">No findings match the current filters.</div>
                ) : (
                    <div className="space-y-2">
                        {filtered.map((f) => {
                            const fix = parseFixProposal(f);
                            const isExpanded = expandedFix === f.id;
                            return (
                                <div
                                    key={f.id}
                                    className={`bg-card rounded-lg border ${f.is_resolved ? 'opacity-50' : ''}`}
                                >
                                    <div className="flex items-start justify-between gap-4 p-4">
                                        <div className="flex-1">
                                            <div className="mb-1 flex flex-wrap items-center gap-2">
                                                <span
                                                    className={`rounded border px-1.5 py-0.5 text-xs font-medium ${severityColor[f.severity] || ''}`}
                                                >
                                                    {f.severity.toUpperCase()}
                                                </span>
                                                <span className="text-muted-foreground text-xs">
                                                    {f.engine} · Level {f.pyramid_level}
                                                </span>
                                                {f.cwe_id && (
                                                    <span className="text-muted-foreground text-xs">{f.cwe_id}</span>
                                                )}
                                                {f.is_accepted_risk && (
                                                    <span className="text-xs text-yellow-400">Risk Accepted</span>
                                                )}
                                                {f.is_resolved && (
                                                    <span className="text-xs text-green-400">Resolved</span>
                                                )}
                                                {fix && (
                                                    <span className="text-xs text-blue-400">Fix Available</span>
                                                )}
                                            </div>
                                            <div className="font-medium">{f.title}</div>
                                            {f.description && (
                                                <div className="text-muted-foreground mt-1 line-clamp-2 text-sm">
                                                    {f.description}
                                                </div>
                                            )}
                                            {f.file_path && (
                                                <div className="text-muted-foreground mt-1 text-xs">
                                                    {f.file_path}
                                                    {f.line_number ? `:${f.line_number}` : ''}
                                                </div>
                                            )}
                                            {f.neural_score != null && (
                                                <div className="text-muted-foreground mt-1 text-xs">
                                                    Neural confidence: {Math.round(f.neural_score * 100)}%
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex shrink-0 flex-wrap items-center gap-2">
                                            {!f.is_resolved && !f.is_accepted_risk && (
                                                <>
                                                    <Button
                                                        disabled={fixLoading === f.id}
                                                        onClick={() =>
                                                            fix
                                                                ? setExpandedFix(isExpanded ? null : f.id)
                                                                : handleGenerateFix(f.id)
                                                        }
                                                        size="sm"
                                                        variant="outline"
                                                    >
                                                        {fixLoading === f.id
                                                            ? 'Generating…'
                                                            : fix
                                                              ? isExpanded
                                                                  ? 'Hide Fix'
                                                                  : 'Show Fix'
                                                              : '✦ Generate Fix'}
                                                    </Button>
                                                    <Button
                                                        disabled={patchLoading === f.id}
                                                        onClick={() =>
                                                            acceptTarget === f.id
                                                                ? setAcceptTarget(null)
                                                                : setAcceptTarget(f.id)
                                                        }
                                                        size="sm"
                                                        variant="outline"
                                                    >
                                                        Accept Risk
                                                    </Button>
                                                    <Button
                                                        disabled={patchLoading === f.id}
                                                        onClick={() => handleResolve(f.id)}
                                                        size="sm"
                                                        variant="outline"
                                                    >
                                                        Resolve
                                                    </Button>
                                                </>
                                            )}
                                        </div>
                                    </div>

                                    {/* Accept Risk inline form */}
                                    {acceptTarget === f.id && (
                                        <div className="border-t px-4 py-3">
                                            <div className="flex items-center gap-2">
                                                <input
                                                    className="bg-background border-input flex-1 rounded-md border px-3 py-1.5 text-sm"
                                                    onChange={(e) => setAcceptNote(e.target.value)}
                                                    placeholder="Justification for accepting this risk…"
                                                    value={acceptNote}
                                                />
                                                <Button
                                                    disabled={patchLoading === f.id}
                                                    onClick={() => handleAcceptRisk(f.id)}
                                                    size="sm"
                                                >
                                                    Confirm
                                                </Button>
                                                <Button
                                                    onClick={() => setAcceptTarget(null)}
                                                    size="sm"
                                                    variant="ghost"
                                                >
                                                    Cancel
                                                </Button>
                                            </div>
                                        </div>
                                    )}

                                    {/* Fix Proposal Panel */}
                                    {fix && isExpanded && (
                                        <div className="border-t p-4">
                                            <div className="mb-3 flex items-center justify-between">
                                                <div className="text-sm font-semibold text-blue-400">
                                                    AI Fix Proposal
                                                </div>
                                                <div className="text-muted-foreground text-xs">
                                                    Confidence: {Math.round(fix.confidence * 100)}% · {fix.generated_by}
                                                </div>
                                            </div>
                                            <p className="text-muted-foreground mb-3 text-sm">{fix.explanation}</p>
                                            <div className="mb-3 grid gap-3 md:grid-cols-2">
                                                <div>
                                                    <div className="text-muted-foreground mb-1 text-xs font-medium uppercase">
                                                        Before
                                                    </div>
                                                    <pre className="bg-red-500/5 rounded border border-red-500/20 p-3 text-xs text-red-300 overflow-x-auto">
                                                        {fix.before_code}
                                                    </pre>
                                                </div>
                                                <div>
                                                    <div className="text-muted-foreground mb-1 text-xs font-medium uppercase">
                                                        After
                                                    </div>
                                                    <pre className="bg-green-500/5 rounded border border-green-500/20 p-3 text-xs text-green-300 overflow-x-auto">
                                                        {fix.after_code}
                                                    </pre>
                                                </div>
                                            </div>
                                            <div className="bg-muted/30 rounded p-3">
                                                <div className="text-muted-foreground mb-1 text-xs font-medium uppercase">
                                                    Rationale
                                                </div>
                                                <p className="text-sm">{fix.rationale}</p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default FindingsPage;
