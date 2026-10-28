import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  RefreshControl, ActivityIndicator,
} from 'react-native';
import { colors, radius, shadows } from '../theme';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../services/api';

const STAT_ICONS = {
  total: 'folder-open-outline',
  new: 'sparkles-outline',
  converted: 'checkmark-circle-outline',
  high_score: 'star-outline',
};

export default function DashboardScreen({ user, onShowToast }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { load(); }, []);

  const onRefresh = () => { setRefreshing(true); load(); };

  if (loading) {
    return (
      <View style={s.center}>
        <ActivityIndicator color={colors.primary} size="large" />
        <Text style={s.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  const kpis = stats ? [
    { key: 'total', label: 'TOTAL LEADS', value: stats.total_leads ?? 0, color: colors.purple },
    { key: 'new', label: 'NEW', value: stats.new_leads ?? 0, color: colors.cyan },
    { key: 'converted', label: 'CONVERTED', value: stats.converted ?? 0, color: colors.emerald },
    { key: 'high_score', label: 'HIGH SCORE', value: stats.high_opportunity_leads ?? stats.high_score_leads ?? 0, color: colors.amber },
  ] : [];

  const statusItems = stats?.status_distribution
    ? stats.status_distribution.map((d) => ({ status: d.status, count: d.count }))
    : stats?.status_breakdown
    ? Object.entries(stats.status_breakdown).map(([status, count]) => ({ status, count }))
    : [
        { status: 'New', count: stats?.new_leads || 0 },
        { status: 'Contacted', count: stats?.contacted || 0 },
        { status: 'Interested', count: stats?.interested || 0 },
        { status: 'Follow-up', count: stats?.follow_up || 0 },
        { status: 'Converted', count: stats?.converted || 0 },
      ];

  return (
    <ScrollView
      style={s.page}
      contentContainerStyle={s.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
    >
      {/* Header */}
      <View style={s.header}>
        <Text style={s.greeting}>Good day, {user?.name?.split(' ')[0] ?? 'Agent'}</Text>
        <Text style={s.subheading}>Your lead pipeline at a glance</Text>
      </View>

      {/* KPI Cards */}
      <View style={s.kpiGrid}>
        {kpis.map((k) => (
          <View key={k.key} style={[s.kpiCard, { borderLeftColor: k.color }]}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <Ionicons name={STAT_ICONS[k.key]} size={16} color={k.color} />
            </View>
            <Text style={s.kpiValue}>{k.value}</Text>
            <Text style={s.kpiLabel}>{k.label}</Text>
          </View>
        ))}
      </View>

      {/* Status Breakdown */}
      {statusItems.length > 0 && (
        <View style={s.section}>
          <Text style={s.sectionTitle}>— STATUS BREAKDOWN —</Text>
          <View style={s.breakdownCard}>
            {statusItems.map(({ status, count }) => (
              <View key={status} style={s.breakdownRow}>
                <Text style={s.breakdownLabel}>{status}</Text>
                <View style={s.breakdownBarWrap}>
                  <View
                    style={[
                      s.breakdownBar,
                      {
                        width: `${Math.min(100, (count / (stats.total_leads || 1)) * 100)}%`,
                        backgroundColor: colors.primary,
                      },
                    ]}
                  />
                </View>
                <Text style={s.breakdownCount}>{count}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Recent Activity hint */}
      <View style={s.tip}>
        <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 6 }}>
          <Ionicons name="bulb-outline" size={15} color={colors.amber} style={{ marginTop: 2 }} />
          <Text style={[s.tipText, { flex: 1 }]}>
            Go to <Text style={s.tipBold}>Search</Text> to find new real-time leads, or{' '}
            <Text style={s.tipBold}>Leads</Text> to manage your pipeline.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.bgPage },
  content: { padding: 12, gap: 10 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bgPage, gap: 12 },
  loadingText: { color: colors.textMuted, fontStyle: 'italic' },

  header: { paddingVertical: 4 },
  greeting: { fontSize: 16, fontWeight: '700', color: colors.textPrimary, letterSpacing: -0.3 },
  subheading: { fontSize: 10, color: colors.textSecondary, marginTop: 2, fontStyle: 'italic' },

  kpiGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  kpiCard: {
    flex: 1,
    minWidth: '44%',
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderColor: colors.borderMedium,
    borderLeftWidth: 3,
    borderRadius: radius.xs,
    padding: 10,
    gap: 2,
    ...shadows.xs,
  },
  kpiIcon: { fontSize: 14 },
  kpiValue: { fontSize: 22, fontWeight: '700', color: colors.textPrimary, letterSpacing: -0.5 },
  kpiLabel: { fontSize: 8, color: colors.textMuted, letterSpacing: 0.8, textTransform: 'uppercase' },

  section: { gap: 8 },
  sectionTitle: {
    fontSize: 10,
    color: colors.textMuted,
    textAlign: 'center',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    fontStyle: 'italic',
  },
  breakdownCard: {
    backgroundColor: colors.bgCard,
    borderWidth: 2,
    borderColor: colors.borderMedium,
    borderRadius: radius.sm,
    padding: 14,
    gap: 10,
    ...shadows.xs,
  },
  breakdownRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  breakdownLabel: { width: 90, fontSize: 11, color: colors.textSecondary },
  breakdownBarWrap: {
    flex: 1,
    height: 6,
    backgroundColor: colors.bgElevated,
    borderRadius: radius.full,
    overflow: 'hidden',
  },
  breakdownBar: { height: '100%', borderRadius: radius.full },
  breakdownCount: { width: 28, fontSize: 12, fontWeight: '700', color: colors.textPrimary, textAlign: 'right' },

  tip: {
    backgroundColor: colors.amberLight,
    borderWidth: 1,
    borderColor: colors.amber,
    borderRadius: radius.xs,
    padding: 12,
    borderStyle: 'dashed',
  },
  tipText: { fontSize: 12, color: colors.amber, lineHeight: 18 },
  tipBold: { fontWeight: '700' },
});
