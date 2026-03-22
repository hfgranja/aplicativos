import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
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
    cwe_id?: string;
    file_path?: string;
    line_number?: number;
    neural_score?: number;
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
                        {filtered.map((f) => (
                            <div
                                key={f.id}
                                className={`bg-card rounded-lg border p-4 ${f.is_resolved ? 'opacity-50' : ''}`}
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1">
                                        <div className="mb-1 flex items-center gap-2">
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
                                    <div className="flex shrink-0 items-center gap-2">
                                        {!f.is_resolved && !f.is_accepted_risk && (
                                            <Button
                                                disabled={patchLoading === f.id}
                                                onClick={() => handleResolve(f.id)}
                                                size="sm"
                                                variant="outline"
                                            >
                                                Resolve
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default FindingsPage;
