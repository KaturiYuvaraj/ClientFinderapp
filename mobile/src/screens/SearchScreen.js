import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, ActivityIndicator, Platform,
} from 'react-native';
import { colors, radius, shadows } from '../theme';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../services/api';
import LeadCard from '../components/LeadCard';

const CATEGORIES = [
  'Restaurant', 'Cafe', 'Salon', 'Clinic', 'Gym', 'Hotel',
  'Dentist', 'Law Firm', 'Real Estate', 'Accounting', 'Auto Repair',
  'Plumbing', 'Roofing', 'HVAC', 'Veterinary', 'Cleaning',
  'Retail', 'Bakery', 'Pharmacy', 'School', 'Photography', 'Marketing Agency',
];

const SERVICES = [
  'Website / Web App', 'Mobile Application', 'Digital Marketing',
  'Website Design', 'SEO Services', 'Social Media Management',
  'Google Ads', 'Logo & Branding', 'E-commerce Store',
  'WhatsApp Chatbot', 'CRM Setup', 'Content Marketing',
  'Video Production', 'Email Marketing', 'Cybersecurity', 'Cloud Setup',
];

const LOCATION_EXAMPLES = [
  { label: '🇺🇸 New York', value: 'New York, USA' },
  { label: '🇺🇸 Los Angeles', value: 'Los Angeles, USA' },
  { label: '🇺🇸 Chicago', value: 'Chicago, USA' },
  { label: '🇺🇸 Miami', value: 'Miami, USA' },
  { label: '🇬🇧 London', value: 'London, UK' },
  { label: '🇬🇧 Manchester', value: 'Manchester, UK' },
  { label: '🇨🇦 Toronto', value: 'Toronto, Canada' },
  { label: '🇦🇺 Sydney', value: 'Sydney, Australia' },
  { label: '🇦🇺 Melbourne', value: 'Melbourne, Australia' },
  { label: '🇦🇪 Dubai', value: 'Dubai, UAE' },
  { label: '🇸🇬 Singapore', value: 'Singapore' },
  { label: '🇩🇪 Berlin', value: 'Berlin, Germany' },
  { label: '🇫🇷 Paris', value: 'Paris, France' },
  { label: '🇮🇳 Mumbai', value: 'Mumbai, India' },
  { label: '🇮🇳 Bangalore', value: 'Bangalore, India' },
  { label: '🇯🇵 Tokyo', value: 'Tokyo, Japan' },
  { label: '🇿🇦 Cape Town', value: 'Cape Town, South Africa' },
  { label: '🇧🇷 São Paulo', value: 'São Paulo, Brazil' },
];

export default function SearchScreen({ onShowToast }) {
  const [location, setLocation] = useState('');
  const [category, setCategory] = useState('');
  const [selectedServices, setSelectedServices] = useState([
    'Website / Web App',
    'Mobile Application',
    'Digital Marketing',
  ]);
  const [keywords, setKeywords] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [filterType, setFilterType] = useState('ALL'); // 'ALL' | 'MISSING_ALL_3' | 'NO_WEBSITE' | 'NO_MOBILE_APP' | 'NO_MARKETING' | 'HAS_PHONE'

  const toggleService = (sv) => {
    setSelectedServices((prev) => {
      if (prev.includes(sv)) {
        if (prev.length === 1) {
          onShowToast('At least one service must remain selected.', 'info');
          return prev;
        }
        return prev.filter((s) => s !== sv);
      } else {
        return [...prev, sv];
      }
    });
  };

  const handleSelectAllServices = () => {
    if (selectedServices.length === SERVICES.length) {
      setSelectedServices(['Website Design']);
    } else {
      setSelectedServices([...SERVICES]);
    }
  };

  const handleSearch = async () => {
    if (!location.trim() || !category.trim()) {
      onShowToast('Please enter a city and category.', 'error');
      return;
    }
    if (selectedServices.length === 0) {
      onShowToast('Please select at least one service.', 'error');
      return;
    }
    setLoading(true);
    setResults([]);
    setSearched(false);
    const serviceStr = selectedServices.join(', ');
    try {
      const data = await api.searchBusinesses({
        location: location.trim(),
        category: category.trim(),
        service: serviceStr,
        services: selectedServices,
        service_offered: serviceStr,
        keywords: keywords.trim(),
      });
      const rawLeads = data.results || data.leads || [];
      const normalized = rawLeads.map((l) => ({
        ...l,
        name: l.name || l.business_name,
        business_name: l.business_name || l.name,
        score: l.lead_score ?? l.opportunity_score ?? l.score ?? 0,
        opportunity_score: l.lead_score ?? l.opportunity_score ?? l.score ?? 0,
        service: l.service || serviceStr,
        service_offered: l.service || serviceStr,
      }));
      setResults(normalized);
      setSearched(true);
      if (normalized.length === 0) {
        onShowToast('No leads found for this search. Try another city or category.', 'info');
      } else {
        onShowToast(`Found ${normalized.length} real-time leads!`, 'success');
      }
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (lead) => {
    try {
      const serviceStr = selectedServices.join(', ');
      await api.saveLead({
        ...lead,
        service: lead.service || serviceStr,
        service_offered: lead.service_offered || serviceStr,
      });
      setResults((prev) =>
        prev.map((l) =>
          (l.provider_id && l.provider_id === lead.provider_id) || l.name === lead.name
            ? { ...l, is_saved: true }
            : l
        )
      );
      onShowToast(`"${lead.name || lead.business_name}" saved to leads!`, 'success');
    } catch (err) {
      onShowToast(err.message, 'error');
    }
  };

  return (
    <ScrollView style={s.page} contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
      {/* Search Form */}
      <View style={s.card}>
        <View style={s.cardHeader}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Ionicons name="globe-outline" size={14} color={colors.primary} />
            <Text style={s.cardTitle}>GLOBAL SEARCH CONSOLE</Text>
            <Ionicons name="globe-outline" size={14} color={colors.primary} />
          </View>
          <Text style={s.cardSub}>Live OSM data · Any city, any country worldwide</Text>
        </View>

        <View style={s.field}>
          <Text style={s.label}>CITY / LOCATION (any country)</Text>
          <TextInput
            style={s.input}
            placeholder="e.g. London UK, Dubai, New York, Tokyo"
            placeholderTextColor={colors.textMuted}
            value={location}
            onChangeText={setLocation}
          />
          {/* Quick-pick world cities */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.chips}>
            {LOCATION_EXAMPLES.map((loc) => (
              <TouchableOpacity
                key={loc.value}
                style={[s.chip, location === loc.value && s.chipActive]}
                onPress={() => setLocation(loc.value)}
              >
                <Text style={[s.chipText, location === loc.value && s.chipTextActive]}>
                  {loc.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        <View style={s.field}>
          <Text style={s.label}>BUSINESS CATEGORY</Text>
          <TextInput
            style={s.input}
            placeholder="e.g. Restaurant, Salon, Clinic"
            placeholderTextColor={colors.textMuted}
            value={category}
            onChangeText={setCategory}
          />
          {/* Quick-pick chips */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.chips}>
            {CATEGORIES.map((c) => (
              <TouchableOpacity
                key={c}
                style={[s.chip, category === c && s.chipActive]}
                onPress={() => setCategory(c)}
              >
                <Text style={[s.chipText, category === c && s.chipTextActive]}>{c}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        <View style={s.field}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
              <Text style={s.label}>YOUR SERVICES</Text>
              <View style={{ backgroundColor: colors.primaryLight, borderColor: colors.primary, borderWidth: 1, borderRadius: 10, paddingHorizontal: 6, paddingVertical: 1 }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: colors.primary }}>
                  {selectedServices.length} Selected
                </Text>
              </View>
            </View>
            <TouchableOpacity onPress={handleSelectAllServices} style={{ paddingHorizontal: 4, paddingVertical: 2 }}>
              <Text style={{ fontSize: 10, color: colors.primary, fontWeight: '700' }}>
                {selectedServices.length === SERVICES.length ? 'Clear to 1' : 'Select All'}
              </Text>
            </TouchableOpacity>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.chips}>
            {SERVICES.map((sv) => {
              const isSelected = selectedServices.includes(sv);
              return (
                <TouchableOpacity
                  key={sv}
                  style={[
                    s.chip,
                    isSelected && {
                      backgroundColor: colors.primaryLight,
                      borderColor: colors.primary,
                      borderWidth: 1.5,
                    }
                  ]}
                  onPress={() => toggleService(sv)}
                  activeOpacity={0.7}
                >
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                    <Ionicons
                      name={isSelected ? 'checkmark-circle' : 'add-circle-outline'}
                      size={13}
                      color={isSelected ? colors.primary : colors.textMuted}
                    />
                    <Text style={[
                      s.chipText,
                      isSelected && { color: colors.primary, fontWeight: '700' }
                    ]}>
                      {sv}
                    </Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        <View style={s.field}>
          <Text style={s.label}>KEYWORDS (optional)</Text>
          <TextInput
            style={s.input}
            placeholder="e.g. no website, new business"
            placeholderTextColor={colors.textMuted}
            value={keywords}
            onChangeText={setKeywords}
          />
        </View>

        <TouchableOpacity
          style={[s.searchBtn, loading && s.btnDisabled]}
          onPress={handleSearch}
          disabled={loading}
        >
          {loading ? (
            <View style={s.btnRow}>
              <ActivityIndicator color={colors.white} size="small" />
              <Text style={s.searchBtnText}>Scanning city data...</Text>
            </View>
          ) : (
            <View style={s.btnRow}>
              <Ionicons name="search" size={14} color={colors.white} />
              <Text style={s.searchBtnText}>SEARCH LEADS</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Results */}
      {searched && (
        <View style={{ gap: 8 }}>
          <View style={s.resultsHeader}>
            <Text style={s.resultsTitle}>
              {results.length > 0
                ? `Found ${results.length} leads in ${location}`
                : 'No leads found'}
            </Text>
          </View>

          {results.length > 0 && (
            <View style={{ flexDirection: 'row', gap: 6, flexWrap: 'wrap' }}>
              <TouchableOpacity
                style={[s.filterChip, filterType === 'ALL' && s.filterChipActive]}
                onPress={() => setFilterType('ALL')}
              >
                <Text style={[s.filterChipText, filterType === 'ALL' && s.filterChipTextActive]}>
                  All ({results.length})
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[s.filterChip, filterType === 'MISSING_ALL_3' && s.filterChipActiveAmber]}
                onPress={() => setFilterType('MISSING_ALL_3')}
              >
                <Text style={[s.filterChipText, filterType === 'MISSING_ALL_3' && { color: colors.amber, fontWeight: '700' }]}>
                  🔥 Missing All 3 ({results.filter((r) => !r.website && !r.has_mobile_app && !r.has_digital_marketing).length})
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[s.filterChip, filterType === 'NO_WEBSITE' && s.filterChipActiveAmber]}
                onPress={() => setFilterType('NO_WEBSITE')}
              >
                <Text style={[s.filterChipText, filterType === 'NO_WEBSITE' && { color: colors.amber, fontWeight: '700' }]}>
                  ❌ No Website/WebApp ({results.filter((r) => !r.website).length})
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[s.filterChip, filterType === 'NO_MOBILE_APP' && s.filterChipActiveAmber]}
                onPress={() => setFilterType('NO_MOBILE_APP')}
              >
                <Text style={[s.filterChipText, filterType === 'NO_MOBILE_APP' && { color: colors.amber, fontWeight: '700' }]}>
                  📵 No Mobile App ({results.filter((r) => !r.has_mobile_app).length})
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[s.filterChip, filterType === 'NO_MARKETING' && s.filterChipActiveAmber]}
                onPress={() => setFilterType('NO_MARKETING')}
              >
                <Text style={[s.filterChipText, filterType === 'NO_MARKETING' && { color: colors.amber, fontWeight: '700' }]}>
                  📉 No Digital Marketing ({results.filter((r) => !r.has_digital_marketing).length})
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[s.filterChip, filterType === 'HAS_PHONE' && s.filterChipActiveCyan]}
                onPress={() => setFilterType('HAS_PHONE')}
              >
                <Text style={[s.filterChipText, filterType === 'HAS_PHONE' && { color: colors.cyan, fontWeight: '700' }]}>
                  📞 Has Phone ({results.filter((r) => !!r.phone).length})
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      )}

      {results
        .filter((lead) => {
          if (filterType === 'MISSING_ALL_3') {
            return !lead.website && !lead.has_mobile_app && !lead.has_digital_marketing;
          }
          if (filterType === 'NO_WEBSITE') return !lead.website;
          if (filterType === 'NO_MOBILE_APP') return !lead.has_mobile_app;
          if (filterType === 'NO_MARKETING') return !lead.has_digital_marketing;
          if (filterType === 'HAS_PHONE') return !!lead.phone;
          return true;
        })
        .map((lead, i) => (
          <LeadCard key={lead.id || i} lead={lead} onSave={handleSave} onShowToast={onShowToast} />
        ))}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.bgPage },
  content: { padding: 12, gap: 10 },

  card: {
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderColor: colors.borderDark,
    borderRadius: radius.xs,
    padding: 12,
    gap: 10,
    ...shadows.sm,
  },
  cardHeader: { alignItems: 'center', paddingBottom: 6, borderBottomWidth: 1, borderBottomColor: colors.borderSubtle, borderStyle: 'dashed' },
  cardTitle: { fontSize: 13, fontWeight: '700', color: colors.primary, letterSpacing: 1.5 },
  cardSub: { fontSize: 10, color: colors.textMuted, fontStyle: 'italic', marginTop: 2 },

  field: { gap: 5 },
  label: { fontSize: 10, color: colors.textMuted, letterSpacing: 0.9, textTransform: 'uppercase' },
  input: {
    backgroundColor: colors.bgPage,
    borderWidth: 1,
    borderBottomWidth: 2,
    borderColor: colors.borderSubtle,
    borderBottomColor: colors.borderDark,
    borderRadius: radius.xs,
    paddingHorizontal: 10,
    paddingVertical: 7,
    fontSize: 12,
    color: colors.textPrimary,
    fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace',
  },
  chips: { marginTop: 6 },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: radius.xs,
    backgroundColor: colors.bgElevated,
    borderWidth: 1,
    borderColor: colors.borderSubtle,
    marginRight: 6,
  },
  chipActive: { backgroundColor: colors.primary, borderColor: colors.borderDark },
  chipText: { fontSize: 11, color: colors.textSecondary },
  chipTextActive: { color: colors.white, fontWeight: '700' },

  searchBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.xs,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colors.borderDark,
    ...shadows.sm,
    marginTop: 2,
  },
  btnDisabled: { opacity: 0.7 },
  btnRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  searchBtnText: { color: colors.white, fontSize: 12, fontWeight: '700', letterSpacing: 1 },

  resultsHeader: { paddingVertical: 4 },
  resultsTitle: { fontSize: 13, fontWeight: '700', color: colors.textPrimary },

  filterChip: {
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: radius.xs,
    backgroundColor: colors.bgElevated,
    borderWidth: 1,
    borderColor: colors.borderMedium,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.borderDark,
  },
  filterChipActiveAmber: {
    backgroundColor: colors.amberLight,
    borderColor: colors.amber,
  },
  filterChipActiveCyan: {
    backgroundColor: colors.cyanLight,
    borderColor: colors.cyan,
  },
  filterChipText: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  filterChipTextActive: {
    color: colors.white,
    fontWeight: '700',
  },
});

