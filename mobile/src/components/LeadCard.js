import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  Linking, Modal, ScrollView, TextInput, Platform, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from '../theme';
import { api } from '../services/api';

const STATUS_OPTIONS = ['New', 'Contacted', 'Interested', 'Follow-up', 'Converted', 'Not Interested'];

const STATUS_COLORS = {
  'New':            { bg: colors.purpleLight, fg: colors.purple },
  'Contacted':      { bg: colors.cyanLight,   fg: colors.cyan },
  'Interested':     { bg: colors.amberLight,  fg: colors.amber },
  'Follow-up':      { bg: colors.primaryLight,fg: colors.primary },
  'Follow Up':      { bg: colors.primaryLight,fg: colors.primary },
  'Converted':      { bg: colors.emeraldLight,fg: colors.emerald },
  'Not Interested': { bg: colors.bgElevated,  fg: colors.textMuted },
};

function ScoreBadge({ score }) {
  const s = Number(score || 0);
  let bg, fg;
  if (s >= 80) { bg = colors.emeraldLight; fg = colors.emerald; }
  else if (s >= 60) { bg = colors.cyanLight; fg = colors.cyan; }
  else if (s >= 40) { bg = colors.amberLight; fg = colors.amber; }
  else { bg = colors.primaryLight; fg = colors.primary; }
  return (
    <View style={[sc.scoreBadge, { backgroundColor: bg, borderColor: fg, transform: [{ rotate: '-1.5deg' }] }]}>
      <Text style={[sc.scoreNum, { color: fg }]}>{s}</Text>
      <Text style={[sc.scoreLabel, { color: fg }]}>SCORE</Text>
    </View>
  );
}

export default function LeadCard({ lead, saved, onSave, onDelete, onStatusChange, onShowToast }) {
  const [currentLead, setCurrentLead] = useState(lead);
  const [enriching, setEnriching] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [showStatusPicker, setShowStatusPicker] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [msgLoading, setMsgLoading] = useState(false);
  const [message, setMessage] = useState('');

  React.useEffect(() => {
    setCurrentLead(lead);
  }, [lead]);

  if (!currentLead) return null;

  const hasWebsite = !!currentLead?.website;
  const hasPhone = !!currentLead?.phone;
  const sc2 = STATUS_COLORS[currentLead?.status] || STATUS_COLORS['New'];

  const handleAutoEnrich = async () => {
    setEnriching(true);
    try {
      if (saved && currentLead.id) {
        const updated = await api.enrichSavedLead(currentLead.id);
        setCurrentLead(updated);
        onShowToast(
          updated.phone || updated.website
            ? `Discovered: ${[updated.phone && `📞 ${updated.phone}`, updated.website && '🌐 Website'].filter(Boolean).join(' · ')}`
            : 'No public contact found online for this location',
          updated.phone || updated.website ? 'success' : 'info'
        );
      } else {
        const res = await api.enrichPreview(currentLead);
        if (res.enriched) {
          const updated = {
            ...currentLead,
            phone: res.phone || currentLead.phone,
            website: res.website || currentLead.website
          };
          setCurrentLead(updated);
          onShowToast(
            `Discovered: ${[res.phone && `📞 ${res.phone}`, res.website && '🌐 Website'].filter(Boolean).join(' · ')}`,
            'success'
          );
        } else {
          onShowToast('Could not find verified online contact for this business', 'info');
        }
      }
    } catch (e) {
      onShowToast(e.message || 'Auto-fetch failed', 'error');
    } finally {
      setEnriching(false);
    }
  };

  const openWebsite = () => {
    if (currentLead?.website) {
      const url = currentLead.website.startsWith('http')
        ? currentLead.website
        : `https://${currentLead.website}`;
      Linking.openURL(url).catch(() => onShowToast('Could not open URL', 'error'));
    }
  };

  const dialPhone = () => {
    if (currentLead?.phone) {
      const clean = String(currentLead.phone).replace(/[^0-9+]/g, '');
      Linking.openURL(`tel:${clean}`).catch(() => onShowToast('Cannot dial this number', 'error'));
    }
  };

  const searchGoogleForPhone = () => {
    const q = encodeURIComponent(`${currentLead.name || currentLead.business_name} ${currentLead.city || currentLead.address || ''} phone number`);
    Linking.openURL(`https://www.google.com/search?q=${q}`);
  };

  const searchGoogleForWebsite = () => {
    const q = encodeURIComponent(`${currentLead.name || currentLead.business_name} ${currentLead.city || ''} official website`);
    Linking.openURL(`https://www.google.com/search?q=${q}`);
  };

  // Google Maps Search finds the official verified business listing
  const openMaps = () => {
    const bizName = currentLead.name || currentLead.business_name || '';
    const loc = currentLead.address || currentLead.city || '';
    const query = encodeURIComponent(`${bizName} ${loc}`.trim());
    const url = `https://www.google.com/maps/search/?api=1&query=${query}`;
    Linking.openURL(url).catch(() => onShowToast('Could not open Google Maps', 'error'));
  };

  // Direct GPS pin fallback
  const openGpsPin = () => {
    if (currentLead.latitude && currentLead.longitude) {
      const url = `https://maps.google.com/?q=${currentLead.latitude},${currentLead.longitude}`;
      Linking.openURL(url).catch(() => onShowToast('Could not open GPS coordinates', 'error'));
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const normalizedBiz = {
        name: currentLead.name || currentLead.business_name || 'Business',
        category: currentLead.category || '',
        phone: currentLead.phone || '',
        website: currentLead.website || '',
        address: currentLead.address || '',
        city: currentLead.city || '',
        latitude: currentLead.latitude ?? 0.0,
        longitude: currentLead.longitude ?? 0.0,
        rating: currentLead.rating ?? 0.0,
        review_count: currentLead.review_count ?? 0,
        source: currentLead.source || 'OpenStreetMap',
        source_url: currentLead.source_url || '',
        provider_id: currentLead.provider_id || null,
      };
      const res = await api.analyzeLead(
        normalizedBiz,
        currentLead.service_offered || currentLead.service || 'Website Design'
      );
      setAnalysis(res);
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateMsg = async () => {
    setMsgLoading(true);
    try {
      const res = await api.generateMessage({
        business_name: currentLead.name || currentLead.business_name || 'Business',
        category: currentLead.category || '',
        location: currentLead.city || currentLead.address || '',
        service: currentLead.service_offered || currentLead.service || 'Website Design',
        opportunity_reason: analysis?.reason || currentLead.opportunity_reason || '',
        verified_facts: analysis?.verified_facts || currentLead.verified_facts || [],
        lead_id: currentLead.id || null,
      });
      setMessage(res.message || '');
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setMsgLoading(false);
    }
  };

  const isSaved = Boolean(saved || currentLead?.is_saved);

  return (
    <>
      <TouchableOpacity style={sc.card} onPress={() => setShowDetail(true)} activeOpacity={0.85}>
        {/* Red margin line */}
        <View style={sc.marginLine} />

        <View style={sc.cardTop}>
          <View style={sc.cardInfo}>
            <Text style={sc.name} numberOfLines={1}>{currentLead.name || currentLead.business_name}</Text>
            <TouchableOpacity onPress={openMaps} activeOpacity={0.7} style={{ flexDirection: 'row', alignItems: 'center', gap: 3, marginTop: 2 }}>
              <Ionicons name="location-outline" size={11} color={colors.emerald} />
              <Text style={[sc.meta, { color: colors.textSecondary }]} numberOfLines={1}>
                {currentLead.category} · {currentLead.city || currentLead.address}
              </Text>
            </TouchableOpacity>

            {/* Explicit Presence Indicators */}
            <View style={{ flexDirection: 'column', gap: 3, marginTop: 5 }}>
              {/* Phone indicator */}
              <TouchableOpacity
                onPress={hasPhone ? dialPhone : searchGoogleForPhone}
                style={[sc.presenceBadge, hasPhone ? sc.presencePhoneOk : sc.presenceNone]}
                activeOpacity={0.7}
              >
                <Ionicons name={hasPhone ? "call" : "call-outline"} size={10} color={hasPhone ? colors.cyan : colors.textMuted} />
                <Text style={[sc.presenceText, { color: hasPhone ? colors.cyan : colors.textMuted }]} numberOfLines={1}>
                  {hasPhone ? `Phone: ${currentLead.phone}` : "Phone: Not Listed"}
                </Text>
              </TouchableOpacity>

              {/* Website indicator */}
              <TouchableOpacity
                onPress={hasWebsite ? openWebsite : undefined}
                disabled={!hasWebsite}
                style={[sc.presenceBadge, hasWebsite ? sc.presenceWebOk : sc.presenceNoneWeb]}
                activeOpacity={hasWebsite ? 0.7 : 1}
              >
                <Ionicons name={hasWebsite ? "globe" : "checkmark-done-circle-outline"} size={10} color={hasWebsite ? colors.purple : colors.emerald} />
                <Text style={[sc.presenceText, { color: hasWebsite ? colors.purple : colors.amber }]} numberOfLines={1}>
                  {hasWebsite
                    ? `Website/WebApp: ${currentLead.website.replace(/^https?:\/\/(www\.)?/, '').slice(0, 24)}`
                    : "✓ Auto-Verified: No Website / Web App"}
                </Text>
              </TouchableOpacity>

              {/* Mobile App & Digital Marketing Gap Badges */}
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 2 }}>
                {!currentLead.has_mobile_app && (
                  <View style={[sc.presenceBadge, sc.presenceNoneWeb]}>
                    <Ionicons name="phone-portrait-outline" size={10} color={colors.amber} />
                    <Text style={[sc.presenceText, { color: colors.amber }]}>✓ No Mobile App</Text>
                  </View>
                )}
                {!currentLead.has_digital_marketing && (
                  <View style={[sc.presenceBadge, sc.presenceNoneWeb]}>
                    <Ionicons name="trending-down-outline" size={10} color={colors.amber} />
                    <Text style={[sc.presenceText, { color: colors.amber }]}>✓ No Digital Marketing</Text>
                  </View>
                )}
              </View>
            </View>
          </View>
          <ScoreBadge score={currentLead.opportunity_score ?? currentLead.lead_score ?? currentLead.score ?? 0} />
        </View>

        {/* Website + Phone + Maps action chips */}
        <View style={sc.chips}>
          {hasWebsite && (
            <TouchableOpacity style={[sc.chip, sc.chipWeb]} onPress={openWebsite}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Ionicons name="globe-outline" size={11} color={colors.purple} />
                <Text style={[sc.chipText, { color: colors.purple, fontWeight: '700' }]}>Visit Website</Text>
              </View>
            </TouchableOpacity>
          )}
          {hasPhone ? (
            <TouchableOpacity style={[sc.chip, sc.chipPhone]} onPress={dialPhone}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Ionicons name="call-outline" size={11} color={colors.cyan} />
                <Text style={[sc.chipText, { color: colors.cyan, fontWeight: '700' }]}>Call</Text>
              </View>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[sc.chip, { backgroundColor: colors.cyanLight, borderColor: colors.cyan }]}
              onPress={handleAutoEnrich}
              disabled={enriching}
            >
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                {enriching ? (
                  <ActivityIndicator size="small" color={colors.cyan} style={{ transform: [{ scale: 0.7 }] }} />
                ) : (
                  <Ionicons name="flash" size={11} color={colors.cyan} />
                )}
                <Text style={[sc.chipText, { color: colors.cyan, fontWeight: '700' }]}>
                  {enriching ? "Fetching..." : "⚡ Auto-Fetch Phone"}
                </Text>
              </View>
            </TouchableOpacity>
          )}
          <TouchableOpacity style={[sc.chip, sc.chipMap]} onPress={openMaps}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
              <Ionicons name="map-outline" size={11} color={colors.emerald} />
              <Text style={[sc.chipText, { color: colors.emerald, fontWeight: '600' }]}>Maps</Text>
            </View>
          </TouchableOpacity>
          {currentLead.status && (
            <View style={[sc.chip, { backgroundColor: sc2.bg, borderColor: sc2.fg }]}>
              <Text style={[sc.chipText, { color: sc2.fg }]}>{currentLead.status}</Text>
            </View>
          )}
        </View>

        {/* Actions */}
        <View style={sc.actions}>
          {!saved && onSave && (
            <TouchableOpacity
              style={[sc.actionBtn, isSaved && { backgroundColor: colors.emeraldLight, borderColor: colors.emerald }]}
              onPress={() => !isSaved && onSave(currentLead)}
              disabled={isSaved}
            >
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                <Ionicons
                  name={isSaved ? "bookmark" : "bookmark-outline"}
                  size={11}
                  color={isSaved ? colors.emerald : colors.textPrimary}
                />
                <Text style={[sc.actionBtnText, isSaved && { color: colors.emerald, fontWeight: '700' }]}>
                  {isSaved ? 'Saved' : 'Save'}
                </Text>
              </View>
            </TouchableOpacity>
          )}
          {saved && onDelete && (
            <TouchableOpacity style={[sc.actionBtn, sc.deleteBtn]} onPress={() => onDelete(currentLead.id)}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                <Ionicons name="trash-outline" size={11} color={colors.primary} />
                <Text style={[sc.actionBtnText, { color: colors.primary }]}>Remove</Text>
              </View>
            </TouchableOpacity>
          )}
          {saved && onStatusChange && (
            <TouchableOpacity style={[sc.actionBtn, sc.statusBtn]} onPress={() => setShowStatusPicker(true)}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 2 }}>
                <Text style={sc.actionBtnText}>Status</Text>
                <Ionicons name="chevron-down" size={10} color={colors.textPrimary} />
              </View>
            </TouchableOpacity>
          )}
          <TouchableOpacity style={[sc.actionBtn, sc.detailBtn]} onPress={() => setShowDetail(true)}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 2 }}>
              <Text style={sc.actionBtnText}>Details</Text>
              <Ionicons name="arrow-forward" size={10} color={colors.textPrimary} />
            </View>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>

      {/* ── Detail Modal ── */}
      <Modal visible={showDetail} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setShowDetail(false)}>
        <View style={sc.modal}>
          <View style={sc.modalHeader}>
            <Text style={sc.modalTitle} numberOfLines={1}>{currentLead.name || currentLead.business_name}</Text>
            <TouchableOpacity onPress={() => setShowDetail(false)} style={sc.closeBtn}>
              <Ionicons name="close" size={18} color={colors.primary} />
            </TouchableOpacity>
          </View>

          <ScrollView contentContainerStyle={sc.modalBody}>
            {/* Info rows */}
            <View style={sc.infoBlock}>
              <View style={sc.infoRow}>
                <Text style={sc.infoLabel}>Category</Text>
                <Text style={sc.infoVal}>{currentLead.category || 'General'}</Text>
              </View>

              <View style={sc.infoRow}>
                <Text style={sc.infoLabel}>Services</Text>
                <Text style={[sc.infoVal, { color: colors.primary, fontWeight: '600' }]}>
                  {currentLead.service_offered || currentLead.service || 'Website Design'}
                </Text>
              </View>

              <TouchableOpacity style={sc.infoRow} onPress={openMaps} activeOpacity={0.7}>
                <Text style={sc.infoLabel}>City</Text>
                <View style={{ flex: 1, flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                  <Text style={[sc.infoVal, { color: colors.emerald }]}>{currentLead.city || 'Unknown'}</Text>
                  <Ionicons name="open-outline" size={11} color={colors.emerald} />
                </View>
              </TouchableOpacity>

              <TouchableOpacity style={sc.infoRow} onPress={openMaps} activeOpacity={0.7}>
                <Text style={sc.infoLabel}>Address</Text>
                <View style={{ flex: 1, flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                  <Text style={[sc.infoVal, { color: colors.emerald }]} numberOfLines={2}>{currentLead.address || currentLead.city}</Text>
                  <Ionicons name="open-outline" size={11} color={colors.emerald} />
                </View>
              </TouchableOpacity>

              <View style={sc.infoRow}>
                <Text style={sc.infoLabel}>Website</Text>
                {currentLead.website ? (
                  <TouchableOpacity onPress={openWebsite} style={{ flex: 1, flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                    <Text style={[sc.infoVal, { color: colors.purple, fontWeight: '700', textDecorationLine: 'underline' }]} numberOfLines={1}>
                      ✓ EXISTS: {currentLead.website}
                    </Text>
                    <Ionicons name="open-outline" size={11} color={colors.purple} />
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity onPress={handleAutoEnrich} style={sc.findPhoneBtn} disabled={enriching}>
                    <Ionicons name="flash-outline" size={12} color={colors.cyan} />
                    <Text style={[sc.findPhoneTxt, { color: colors.cyan, fontWeight: '700' }]}>
                      {enriching ? "Fetching..." : "⚡ Tap to Auto-Fetch Website"}
                    </Text>
                  </TouchableOpacity>
                )}
              </View>

              {/* Phone row — tappable to dial or auto-fetch */}
              <View style={sc.infoRow}>
                <Text style={sc.infoLabel}>Phone</Text>
                {hasPhone ? (
                  <TouchableOpacity onPress={dialPhone} style={{ flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <Text style={[sc.infoVal, { color: colors.cyan, fontWeight: '700' }]}>
                      ✓ EXISTS: 📞 {currentLead.phone}
                    </Text>
                    <Ionicons name="call" size={12} color={colors.cyan} />
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity onPress={handleAutoEnrich} style={sc.findPhoneBtn} disabled={enriching}>
                    <Ionicons name="flash-outline" size={12} color={colors.cyan} />
                    <Text style={[sc.findPhoneTxt, { color: colors.cyan, fontWeight: '700' }]}>
                      {enriching ? "Fetching..." : "⚡ Tap to Auto-Fetch Phone"}
                    </Text>
                  </TouchableOpacity>
                )}
              </View>

              <View style={[sc.infoRow, { borderBottomWidth: 0 }]}>
                <Text style={sc.infoLabel}>Source</Text>
                <Text style={sc.infoVal}>{currentLead.source || 'OpenStreetMap Live'}</Text>
              </View>
            </View>

            {/* Direct Auto-Enrich Action Button when contacts are missing */}
            {(!hasPhone || !hasWebsite) && (
              <TouchableOpacity
                style={[sc.analyzeBtn, { backgroundColor: colors.cyan, marginBottom: 12 }, enriching && { opacity: 0.7 }]}
                onPress={handleAutoEnrich}
                disabled={enriching}
              >
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  {enriching ? (
                    <ActivityIndicator size="small" color={colors.white} />
                  ) : (
                    <Ionicons name="flash" size={15} color={colors.white} />
                  )}
                  <Text style={sc.analyzeBtnText}>
                    {enriching ? "Searching Online for Contact Details..." : "⚡ Auto-Fetch Phone & Website Directly"}
                  </Text>
                </View>
              </TouchableOpacity>
            )}

            {/* AI Analysis */}
            {!analysis ? (
              <TouchableOpacity
                style={[sc.analyzeBtn, analyzing && { opacity: 0.7 }]}
                onPress={handleAnalyze}
                disabled={analyzing}
              >
                {analyzing ? (
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <ActivityIndicator size="small" color={colors.white} />
                    <Text style={sc.analyzeBtnText}>Analyzing Lead...</Text>
                  </View>
                ) : (
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <Ionicons name="sparkles" size={15} color={colors.white} />
                    <Text style={sc.analyzeBtnText}>AI Analyze This Lead</Text>
                  </View>
                )}
              </TouchableOpacity>
            ) : (
              <View style={sc.analysisBox}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                  <Ionicons name="sparkles" size={14} color={colors.primary} />
                  <Text style={sc.analysisTitle}>AI Analysis</Text>
                </View>
                {(analysis.opportunity_type || analysis.reason || analysis.opportunity) && (
                  <View style={sc.opportunityBox}>
                    <Text style={sc.opTitle}>
                      {analysis.opportunity_type || analysis.opportunity?.title || 'Opportunity Identified'}
                    </Text>
                    <Text style={sc.opDesc}>
                      {analysis.reason || analysis.opportunity?.description || ''}
                    </Text>
                  </View>
                )}
                {((analysis.verified_facts && analysis.verified_facts.length > 0) ||
                  (analysis.facts && analysis.facts.length > 0) ||
                  (analysis.inferences && analysis.inferences.length > 0)) && (
                  <View style={sc.factsBox}>
                    {(analysis.verified_facts || analysis.facts || []).map((f, i) => (
                      <View key={i} style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 5 }}>
                        <Ionicons name="checkmark-circle-outline" size={13} color={colors.emerald} style={{ marginTop: 2 }} />
                        <Text style={[sc.factItem, { flex: 1 }]}>{f}</Text>
                      </View>
                    ))}
                    {(analysis.inferences || []).map((inf, i) => (
                      <View key={'inf' + i} style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 5 }}>
                        <Ionicons name="arrow-forward-circle-outline" size={13} color={colors.primary} style={{ marginTop: 2 }} />
                        <Text style={[sc.inferItem, { flex: 1 }]}>{inf}</Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            )}

            {/* Message Generator */}
            <View style={sc.msgSection}>
              <TouchableOpacity
                style={[sc.analyzeBtn, { backgroundColor: colors.cyan }, msgLoading && { opacity: 0.7 }]}
                onPress={handleGenerateMsg}
                disabled={msgLoading}
              >
                {msgLoading ? (
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <ActivityIndicator size="small" color={colors.white} />
                    <Text style={sc.analyzeBtnText}>Writing Message...</Text>
                  </View>
                ) : (
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <Ionicons name="mail-outline" size={15} color={colors.white} />
                    <Text style={sc.analyzeBtnText}>Generate Outreach Message</Text>
                  </View>
                )}
              </TouchableOpacity>
              {message.length > 0 && (
                <View style={sc.msgBox}>
                  <Text style={sc.msgText}>{message}</Text>
                </View>
              )}
            </View>

            {/* Map & Lookup buttons */}
            <View style={{ gap: 8 }}>
              <View style={sc.linkRow}>
                <TouchableOpacity style={[sc.linkBtn, { backgroundColor: colors.emeraldLight, borderColor: colors.emerald }]} onPress={openMaps}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                    <Ionicons name="map-outline" size={13} color={colors.emerald} />
                    <Text style={[sc.linkBtnText, { color: colors.emerald }]}>Open Google Maps</Text>
                  </View>
                </TouchableOpacity>
                {!hasPhone && (
                  <TouchableOpacity style={[sc.linkBtn, { backgroundColor: colors.primaryLight, borderColor: colors.primary }]} onPress={searchGoogleForPhone}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                      <Ionicons name="call-outline" size={13} color={colors.primary} />
                      <Text style={[sc.linkBtnText, { color: colors.primary }]}>Find Phone</Text>
                    </View>
                  </TouchableOpacity>
                )}
                {!hasWebsite && (
                  <TouchableOpacity style={[sc.linkBtn, { backgroundColor: colors.amberLight, borderColor: colors.amber }]} onPress={searchGoogleForWebsite}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                      <Ionicons name="globe-outline" size={13} color={colors.amber} />
                      <Text style={[sc.linkBtnText, { color: colors.amber }]}>Find Website</Text>
                    </View>
                  </TouchableOpacity>
                )}
                {currentLead.website && (
                  <TouchableOpacity style={sc.linkBtn} onPress={openWebsite}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                      <Ionicons name="globe-outline" size={13} color={colors.purple} />
                      <Text style={sc.linkBtnText}>Website</Text>
                    </View>
                  </TouchableOpacity>
                )}
              </View>

              {currentLead.latitude && currentLead.longitude && (
                <TouchableOpacity style={[sc.linkBtn, { backgroundColor: colors.bgElevated, borderColor: colors.borderMedium }]} onPress={openGpsPin}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5 }}>
                    <Ionicons name="navigate-outline" size={12} color={colors.textSecondary} />
                    <Text style={[sc.linkBtnText, { color: colors.textSecondary }]}>
                      GPS Coordinates ({Number(currentLead.latitude).toFixed(4)}, {Number(currentLead.longitude).toFixed(4)})
                    </Text>
                  </View>
                </TouchableOpacity>
              )}
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* ── Status Picker Modal ── */}
      <Modal visible={showStatusPicker} animationType="fade" transparent onRequestClose={() => setShowStatusPicker(false)}>
        <TouchableOpacity style={sc.overlay} activeOpacity={1} onPress={() => setShowStatusPicker(false)}>
          <View style={sc.picker}>
            <Text style={sc.pickerTitle}>Change Status</Text>
            {STATUS_OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt}
                style={sc.pickerItem}
                onPress={() => { onStatusChange && onStatusChange(opt); setShowStatusPicker(false); }}
              >
                <Text style={sc.pickerItemText}>{opt}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </TouchableOpacity>
      </Modal>
    </>
  );
}

const sc = StyleSheet.create({
  card: {
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderColor: colors.borderMedium,
    borderRadius: radius.xs,
    padding: 10,
    paddingLeft: 14,
    gap: 7,
    ...shadows.xs,
    position: 'relative',
    overflow: 'hidden',
  },
  marginLine: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: 0,
    width: 3,
    backgroundColor: colors.bgElevated,
  },
  cardTop: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  cardInfo: { flex: 1 },
  name: { fontSize: 12, fontWeight: '700', color: colors.textPrimary },
  meta: { fontSize: 10, color: colors.textSecondary, marginTop: 1 },
  phone: { fontSize: 10, color: colors.cyan, marginTop: 1, fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace' },

  presenceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 7,
    paddingVertical: 2.5,
    borderRadius: radius.xs,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  presencePhoneOk: {
    backgroundColor: colors.cyanLight,
    borderColor: colors.cyan,
  },
  presenceWebOk: {
    backgroundColor: colors.purpleLight,
    borderColor: colors.purple,
  },
  presenceNone: {
    backgroundColor: colors.bgElevated,
    borderColor: colors.borderMedium,
    borderStyle: 'dashed',
  },
  presenceNoneWeb: {
    backgroundColor: colors.amberLight,
    borderColor: colors.amber,
  },
  presenceText: {
    fontSize: 9.5,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace',
  },

  scoreBadge: {
    alignItems: 'center',
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: radius.xs,
    borderWidth: 1,
    minWidth: 42,
  },
  scoreNum: { fontSize: 13, fontWeight: '700', fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace' },
  scoreLabel: { fontSize: 6, letterSpacing: 0.8, textTransform: 'uppercase' },

  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.xs, borderWidth: 1, borderColor: colors.borderSubtle, backgroundColor: colors.bgElevated },
  chipWeb: { backgroundColor: colors.purpleLight, borderColor: colors.purple },
  chipNoWeb: { backgroundColor: colors.amberLight, borderColor: colors.amber },
  chipPhone: { backgroundColor: colors.cyanLight, borderColor: colors.cyan },
  chipNoPhone: { backgroundColor: colors.bgElevated, borderColor: colors.borderMedium, borderStyle: 'dashed' },
  chipMap: { backgroundColor: colors.emeraldLight, borderColor: colors.emerald },
  chipText: { fontSize: 10 },
  findPhoneBtn: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  findPhoneTxt: { fontSize: 12, color: colors.primary, fontStyle: 'italic', textDecorationLine: 'underline' },

  actions: { flexDirection: 'row', gap: 5, borderTopWidth: 1, borderTopColor: colors.borderSubtle, borderStyle: 'dashed', paddingTop: 7 },
  actionBtn: { flex: 1, paddingVertical: 5, alignItems: 'center', backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.borderMedium, borderRadius: radius.xs },
  deleteBtn: { backgroundColor: colors.primaryLight, borderColor: colors.primary },
  statusBtn: { backgroundColor: colors.cyanLight, borderColor: colors.cyan },
  detailBtn: { backgroundColor: colors.bgCard },
  actionBtnText: { fontSize: 9, fontWeight: '600', color: colors.textPrimary },

  // Modal
  modal: { flex: 1, backgroundColor: colors.bgCard },
  modalHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    padding: 16, borderBottomWidth: 2, borderBottomColor: colors.borderDark,
    backgroundColor: colors.bgElevated,
    paddingTop: Platform.OS === 'ios' ? 56 : 16,
  },
  modalTitle: { flex: 1, fontSize: 17, fontWeight: '700', color: colors.textPrimary },
  closeBtn: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bgPage, borderWidth: 1, borderColor: colors.borderMedium, borderRadius: radius.xs },
  closeBtnText: { color: colors.primary, fontWeight: '700' },
  modalBody: { padding: 16, gap: 14 },

  infoBlock: { backgroundColor: colors.bgPage, borderWidth: 1, borderColor: colors.borderSubtle, borderRadius: radius.xs, overflow: 'hidden' },
  infoRow: { flexDirection: 'row', padding: 10, borderBottomWidth: 1, borderBottomColor: colors.borderSubtle, gap: 10 },
  infoLabel: { width: 72, fontSize: 11, color: colors.textMuted, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5 },
  infoVal: { flex: 1, fontSize: 12, color: colors.textPrimary },

  analyzeBtn: {
    backgroundColor: colors.primary, borderRadius: radius.xs, paddingVertical: 12,
    alignItems: 'center', borderWidth: 1, borderColor: colors.borderDark, ...shadows.xs,
  },
  analyzeBtnText: { color: colors.white, fontWeight: '700', fontSize: 13 },

  analysisBox: { gap: 10 },
  analysisTitle: { fontSize: 13, fontWeight: '700', color: colors.textPrimary, letterSpacing: 0.3 },
  opportunityBox: {
    backgroundColor: '#fffdf5', borderLeftWidth: 4, borderLeftColor: colors.primary,
    borderWidth: 1, borderColor: colors.borderSubtle, borderStyle: 'dashed',
    borderRadius: radius.xs, padding: 12, gap: 4,
  },
  opTitle: { fontSize: 11, fontWeight: '700', color: colors.textPrimary, textTransform: 'uppercase', letterSpacing: 0.5 },
  opDesc: { fontSize: 12, color: colors.textSecondary, fontStyle: 'italic', lineHeight: 18 },
  factsBox: { gap: 5 },
  factItem: { fontSize: 12, color: colors.emerald },
  inferItem: { fontSize: 12, color: colors.primary },

  msgSection: { gap: 10 },
  msgBox: {
    backgroundColor: '#fffef8', borderWidth: 1, borderColor: colors.borderMedium,
    borderRadius: radius.xs, padding: 12,
  },
  msgText: { fontSize: 12, color: colors.textPrimary, lineHeight: 20 },

  linkRow: { flexDirection: 'row', gap: 10 },
  linkBtn: {
    flex: 1, paddingVertical: 10, alignItems: 'center',
    backgroundColor: colors.purpleLight, borderWidth: 1, borderColor: colors.purple,
    borderRadius: radius.xs,
  },
  linkBtnText: { fontSize: 12, fontWeight: '600', color: colors.purple },

  // Status picker
  overlay: { flex: 1, backgroundColor: 'rgba(26,15,0,0.5)', justifyContent: 'flex-end' },
  picker: {
    backgroundColor: colors.bgCard, borderTopWidth: 2, borderTopColor: colors.borderDark,
    borderRadius: radius.md, padding: 16, gap: 2,
    paddingBottom: Platform.OS === 'ios' ? 32 : 16,
  },
  pickerTitle: { fontSize: 13, fontWeight: '700', color: colors.textPrimary, textAlign: 'center', marginBottom: 8, letterSpacing: 0.5 },
  pickerItem: { paddingVertical: 13, borderBottomWidth: 1, borderBottomColor: colors.borderSubtle },
  pickerItemText: { fontSize: 14, color: colors.textPrimary, textAlign: 'center' },
});
