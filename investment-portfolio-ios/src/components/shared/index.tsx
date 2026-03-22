import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import { Colors, Spacing, Radius, FontSize } from '../../constants/colors';

// ─── Card ────────────────────────────────────────────────────────────────────

interface CardProps {
  children: React.ReactNode;
  style?: object;
  onPress?: () => void;
}

export function Card({ children, style, onPress }: CardProps) {
  if (onPress) {
    return (
      <TouchableOpacity
        style={[styles.card, style]}
        onPress={onPress}
        activeOpacity={0.7}
      >
        {children}
      </TouchableOpacity>
    );
  }
  return <View style={[styles.card, style]}>{children}</View>;
}

// ─── StatCard ────────────────────────────────────────────────────────────────

interface StatCardProps {
  label: string;
  value: string;
  subtitle?: string;
  icon?: string;
  color?: string;
  trend?: 'up' | 'down' | 'neutral';
  style?: object;
}

export function StatCard({ label, value, subtitle, icon, color, trend, style }: StatCardProps) {
  const trendColor =
    trend === 'up' ? Colors.success :
    trend === 'down' ? Colors.danger :
    Colors.textSecondary;

  return (
    <Card style={[styles.statCard, style]}>
      <View style={styles.statHeader}>
        {icon && <Text style={styles.statIcon}>{icon}</Text>}
        <Text style={styles.statLabel}>{label}</Text>
      </View>
      <Text style={[styles.statValue, color ? { color } : {}]}>{value}</Text>
      {subtitle && (
        <Text style={[styles.statSubtitle, trend ? { color: trendColor } : {}]}>
          {trend === 'up' ? '▲ ' : trend === 'down' ? '▼ ' : ''}{subtitle}
        </Text>
      )}
    </Card>
  );
}

// ─── ProgressBar ─────────────────────────────────────────────────────────────

interface ProgressBarProps {
  progress: number;        // 0-100
  color?: string;
  height?: number;
  showLabel?: boolean;
  label?: string;
  style?: object;
}

export function ProgressBar({ progress, color, height = 8, showLabel, label, style }: ProgressBarProps) {
  const clampedProgress = Math.min(100, Math.max(0, progress));
  const barColor = color || Colors.accent;

  return (
    <View style={[styles.progressContainer, style]}>
      {showLabel && (
        <View style={styles.progressLabelRow}>
          {label && <Text style={styles.progressLabel}>{label}</Text>}
          <Text style={[styles.progressPct, { color: barColor }]}>{clampedProgress.toFixed(1)}%</Text>
        </View>
      )}
      <View style={[styles.progressTrack, { height }]}>
        <View
          style={[
            styles.progressFill,
            {
              width: `${clampedProgress}%` as any,
              backgroundColor: barColor,
              height,
              borderRadius: height / 2,
            },
          ]}
        />
      </View>
    </View>
  );
}

// ─── RiskBadge ───────────────────────────────────────────────────────────────

interface RiskBadgeProps {
  level: 1 | 2 | 3 | 4 | 5;
  style?: object;
}

const RISK_LABELS = ['', 'Baixíssimo', 'Baixo', 'Médio', 'Alto', 'Muito Alto'];
const RISK_COLORS = [
  '',
  Colors.risk1,
  Colors.risk2,
  Colors.risk3,
  Colors.risk4,
  Colors.risk5,
];

export function RiskBadge({ level, style }: RiskBadgeProps) {
  const color = RISK_COLORS[level] || Colors.textMuted;
  const label = RISK_LABELS[level] || 'Desconhecido';

  return (
    <View style={[styles.badge, { borderColor: color, backgroundColor: `${color}18` }, style]}>
      <Text style={[styles.badgeText, { color }]}>{'●'.repeat(level)}{'○'.repeat(5 - level)} {label}</Text>
    </View>
  );
}

// ─── LoadingSpinner ───────────────────────────────────────────────────────────

interface LoadingSpinnerProps {
  text?: string;
  style?: object;
}

export function LoadingSpinner({ text, style }: LoadingSpinnerProps) {
  return (
    <View style={[styles.loadingContainer, style]}>
      <ActivityIndicator color={Colors.accent} size="large" />
      {text && <Text style={styles.loadingText}>{text}</Text>}
    </View>
  );
}

// ─── SectionHeader ────────────────────────────────────────────────────────────

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  action?: { label: string; onPress: () => void };
}

export function SectionHeader({ title, subtitle, action }: SectionHeaderProps) {
  return (
    <View style={styles.sectionHeader}>
      <View style={{ flex: 1 }}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {subtitle && <Text style={styles.sectionSubtitle}>{subtitle}</Text>}
      </View>
      {action && (
        <TouchableOpacity onPress={action.onPress}>
          <Text style={styles.sectionAction}>{action.label}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

// ─── PillButton ────────────────────────────────────────────────────────────────

interface PillButtonProps {
  label: string;
  selected?: boolean;
  onPress: () => void;
  color?: string;
}

export function PillButton({ label, selected, onPress, color }: PillButtonProps) {
  const activeColor = color || Colors.accent;

  return (
    <TouchableOpacity
      style={[
        styles.pill,
        selected
          ? { backgroundColor: activeColor, borderColor: activeColor }
          : { backgroundColor: 'transparent', borderColor: Colors.border },
      ]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Text style={[styles.pillText, selected ? { color: '#fff' } : { color: Colors.textSecondary }]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

// ─── EmptyState ──────────────────────────────────────────────────────────────

interface EmptyStateProps {
  icon: string;
  title: string;
  description: string;
  action?: { label: string; onPress: () => void };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyIcon}>{icon}</Text>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyDesc}>{description}</Text>
      {action && (
        <TouchableOpacity style={styles.emptyButton} onPress={action.onPress}>
          <Text style={styles.emptyButtonText}>{action.label}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  statCard: {
    flex: 1,
  },
  statHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    marginBottom: Spacing.xs,
  },
  statIcon: {
    fontSize: FontSize.md,
  },
  statLabel: {
    color: Colors.textMuted,
    fontSize: FontSize.xs,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statValue: {
    color: Colors.text,
    fontSize: FontSize.xl,
    fontWeight: '700',
    marginBottom: 2,
  },
  statSubtitle: {
    color: Colors.textSecondary,
    fontSize: FontSize.xs,
  },
  progressContainer: {
    gap: Spacing.xs,
  },
  progressLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  progressLabel: {
    color: Colors.textSecondary,
    fontSize: FontSize.sm,
  },
  progressPct: {
    fontSize: FontSize.sm,
    fontWeight: '600',
  },
  progressTrack: {
    backgroundColor: Colors.bgCardHover,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    position: 'absolute',
    left: 0,
    top: 0,
  },
  badge: {
    borderRadius: Radius.full,
    borderWidth: 1,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    alignSelf: 'flex-start',
  },
  badgeText: {
    fontSize: FontSize.xs,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: Spacing.md,
    padding: Spacing.xl,
  },
  loadingText: {
    color: Colors.textSecondary,
    fontSize: FontSize.sm,
    textAlign: 'center',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: Spacing.md,
  },
  sectionTitle: {
    color: Colors.text,
    fontSize: FontSize.lg,
    fontWeight: '700',
  },
  sectionSubtitle: {
    color: Colors.textMuted,
    fontSize: FontSize.sm,
    marginTop: 2,
  },
  sectionAction: {
    color: Colors.accentLight,
    fontSize: FontSize.sm,
    fontWeight: '600',
  },
  pill: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs + 2,
    borderRadius: Radius.full,
    borderWidth: 1,
  },
  pillText: {
    fontSize: FontSize.sm,
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
    gap: Spacing.md,
  },
  emptyIcon: {
    fontSize: 48,
  },
  emptyTitle: {
    color: Colors.text,
    fontSize: FontSize.lg,
    fontWeight: '700',
    textAlign: 'center',
  },
  emptyDesc: {
    color: Colors.textSecondary,
    fontSize: FontSize.sm,
    textAlign: 'center',
    lineHeight: 20,
  },
  emptyButton: {
    backgroundColor: Colors.accent,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    marginTop: Spacing.sm,
  },
  emptyButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: FontSize.sm,
  },
});
