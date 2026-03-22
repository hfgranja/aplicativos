import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from '@/components/ui/breadcrumb';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';

interface AuditEvent {
    id: number;
    user_id?: number;
    action: string;
    resource_type: string;
    resource_id: string;
    payload: unknown;
    ip_address: string;
    created_at: string;
}

const AuditTrailPage = () => {
    const [events, setEvents] = useState<AuditEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionFilter, setActionFilter] = useState('');
    const [resourceFilter, setResourceFilter] = useState('');

    const fetchEvents = () => {
        setLoading(true);
        const params = new URLSearchParams();
        if (actionFilter) params.set('action', actionFilter);
        if (resourceFilter) params.set('resource_type', resourceFilter);
        fetch(`/api/v1/pyramid/audit/?${params}`)
            .then((r) => r.json())
            .then((d) => setEvents(d.data?.events || []))
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchEvents();
    }, [actionFilter, resourceFilter]);

    const uniqueActions = [...new Set(events.map((e) => e.action))];
    const uniqueResources = [...new Set(events.map((e) => e.resource_type))];

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
                            <BreadcrumbPage>Audit Trail</BreadcrumbPage>
                        </BreadcrumbItem>
                    </BreadcrumbList>
                </Breadcrumb>
            </header>

            <div className="flex-1 overflow-auto p-6">
                <div className="mb-6">
                    <h1 className="text-2xl font-bold">Immutable Audit Trail</h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        Complete record of all security-relevant actions across the platform
                    </p>
                </div>

                {/* Filters */}
                <div className="mb-4 flex flex-wrap items-center gap-3">
                    <select
                        className="bg-background border-input rounded-md border px-3 py-1.5 text-sm"
                        onChange={(e) => setActionFilter(e.target.value)}
                        value={actionFilter}
                    >
                        <option value="">All actions</option>
                        {uniqueActions.map((a) => (
                            <option
                                key={a}
                                value={a}
                            >
                                {a}
                            </option>
                        ))}
                    </select>
                    <select
                        className="bg-background border-input rounded-md border px-3 py-1.5 text-sm"
                        onChange={(e) => setResourceFilter(e.target.value)}
                        value={resourceFilter}
                    >
                        <option value="">All resource types</option>
                        {uniqueResources.map((r) => (
                            <option
                                key={r}
                                value={r}
                            >
                                {r}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Events */}
                {loading ? (
                    <div className="text-muted-foreground py-10 text-center">Loading audit events…</div>
                ) : events.length === 0 ? (
                    <div className="text-muted-foreground py-10 text-center">No audit events found.</div>
                ) : (
                    <div className="bg-card rounded-lg border">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-muted-foreground px-4 py-3 text-left font-medium">Time</th>
                                    <th className="text-muted-foreground px-4 py-3 text-left font-medium">Action</th>
                                    <th className="text-muted-foreground px-4 py-3 text-left font-medium">Resource</th>
                                    <th className="text-muted-foreground px-4 py-3 text-left font-medium">Resource ID</th>
                                    <th className="text-muted-foreground px-4 py-3 text-left font-medium">IP</th>
                                </tr>
                            </thead>
                            <tbody>
                                {events.map((e) => (
                                    <tr
                                        key={e.id}
                                        className="hover:bg-muted/30 border-b last:border-0"
                                    >
                                        <td className="text-muted-foreground px-4 py-3 text-xs">
                                            {new Date(e.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className="bg-muted rounded px-1.5 py-0.5 font-mono text-xs">
                                                {e.action}
                                            </span>
                                        </td>
                                        <td className="text-muted-foreground px-4 py-3 text-xs">{e.resource_type}</td>
                                        <td className="text-muted-foreground px-4 py-3 font-mono text-xs">
                                            {e.resource_id || '—'}
                                        </td>
                                        <td className="text-muted-foreground px-4 py-3 text-xs">
                                            {e.ip_address || '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AuditTrailPage;
