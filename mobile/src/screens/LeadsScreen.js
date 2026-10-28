import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity,
  TextInput, RefreshControl, ActivityIndicator, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from '../theme';
import { api } from '../services/api';
import LeadCard from '../components/LeadCard';

const STATUS_FILTERS = ['All', 'New', 'Contacted', 'Interested', 'Follow-up', 'Converted', 'Not Interested'];

export default function LeadsScreen({ onShowToast }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('All');

  const load = async () => {
    try {
      const data = await api.getSavedLeads({ status, search });
      const normalized = (data || []).map((l) => ({
        ...l,
        name: l.business_name || l.name,
        business_name: l.business_name || l.name,
        score: l.lead_score ?? l.opportunity_score ?? l.score ?? 0,
        opportunity_score: l.lead_score ?? l.opportunity_score ?? l.score ?? 0,
      }));
      setLeads(normalized);
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { setLoading(true); load(); }, [status, search]);

  const onRefresh = () => { setRefreshing(true); load(); };

  const handleDelete = async (id) => {
    try {
      await api.deleteLead(id);
      setLeads((prev) => prev.filter((l) => l.id !== id));
      onShowToast('Lead removed.', 'info');
    } catch (err) {
      onShowToast(err.message, 'error');
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      await api.updateLead(id, { status: newStatus });
      setLeads((prev) => prev.map((l) => (l.id === id ? { ...l, status: newStatus } : l)));
      onShowToast(`Status updated to "${newStatus}"`, 'success');
    } catch (err) {
      onShowToast(err.message, 'error');
    }
  };

  return (
    <View style={s.page}>
      {/* Search bar */}
      <View style={s.topBar}>
        <TextInput
          style={s.searchInput}
          placeholder="Search leads..."
          placeholderTextColor={colors.textMuted}
          value={search}
          onChangeText={setSearch}
        />
      </View>

      {/* Status filter chips */}
      <FlatList
        data={STATUS_FILTERS}
        horizontal
        showsHorizontalScrollIndicator={false}
        keyExtractor={(i) => i}
        style={s.filterBar}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 6 }}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[s.filterChip, status === item && s.filterChipActive]}
            onPress={() => setStatus(item)}
          >
            <Text style={[s.filterChipText, status === item && s.filterChipTextActive]}>
              {item}
            </Text>
          </TouchableOpacity>
        )}
      />

      {loading ? (
        <View style={s.center}>
          <ActivityIndicator color={colors.primary} size="large" />
          <Text style={s.loadingText}>Loading leads...</Text>
        </View>
      ) : leads.length === 0 ? (
        <View style={s.empty}>
          <Ionicons name="file-tray-outline" size={40} color={colors.textMuted} />
          <Text style={s.emptyTitle}>No leads yet</Text>
          <Text style={s.emptyDesc}>Search for businesses and save them here.</Text>
        </View>
      ) : (
        <FlatList
          data={leads}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={s.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
          renderItem={({ item }) => (
            <LeadCard
              lead={item}
              saved
              onDelete={() => handleDelete(item.id)}
              onStatusChange={(s) => handleStatusChange(item.id, s)}
              onShowToast={onShowToast}
            />
          )}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.bgPage },
  topBar: { padding: 12, paddingBottom: 6 },
  searchInput: {
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderBottomWidth: 2,
    borderColor: colors.borderSubtle,
    borderBottomColor: colors.borderDark,
    borderRadius: radius.xs,
    paddingHorizontal: 12,
    paddingVertical: 9,
    fontSize: 13,
    color: colors.textPrimary,
    fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace',
  },
  filterBar: { flexGrow: 0, marginBottom: 6 },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: radius.xs,
    backgroundColor: colors.bgElevated,
    borderWidth: 1,
    borderColor: colors.borderSubtle,
  },
  filterChipActive: { backgroundColor: colors.primary, borderColor: colors.borderDark },
  filterChipText: { fontSize: 11, color: colors.textSecondary, fontWeight: '500' },
  filterChipTextActive: { color: colors.white, fontWeight: '700' },
  list: { padding: 12, gap: 10 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10 },
  loadingText: { color: colors.textMuted, fontStyle: 'italic' },
  empty: {
    flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10,
    paddingHorizontal: 40,
  },
  emptyIcon: { fontSize: 36 },
  emptyTitle: { fontSize: 14, fontWeight: '700', color: colors.textPrimary },
  emptyDesc: { fontSize: 11, color: colors.textMuted, textAlign: 'center', fontStyle: 'italic' },
});
