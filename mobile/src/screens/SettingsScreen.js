import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, Switch, Platform, Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from '../theme';
import { api } from '../services/api';

export default function SettingsScreen({ user, onLogout, onShowToast }) {
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');
  const [saving, setSaving] = useState(false);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api.getBaseUrl().then(setApiUrl);
  }, []);

  const saveApiUrl = async () => {
    setSaving(true);
    try {
      await api.setBaseUrl(apiUrl.trim());
      onShowToast('API URL saved!', 'success');
    } catch {
      onShowToast('Failed to save URL', 'error');
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    try {
      const res = await api.checkHealth();
      setHealth({ ok: true, msg: res?.status === 'healthy' ? `Connected ✓ (${res.business_provider || 'active'})` : 'Connected ✓' });
      onShowToast('Backend connected!', 'success');
    } catch (err) {
      setHealth({ ok: false, msg: err.message });
      onShowToast('Connection failed', 'error');
    }
  };

  const handleLogout = async () => {
    if (Platform.OS === 'web') {
      if (window.confirm('Are you sure you want to sign out?')) {
        await api.logout();
        onLogout();
      }
      return;
    }
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await api.logout();
          onLogout();
        },
      },
    ]);
  };

  return (
    <ScrollView style={s.page} contentContainerStyle={s.content}>
      {/* Profile */}
      <View style={s.card}>
        <Text style={s.sectionTitle}>— ACCOUNT —</Text>
        <View style={s.profileRow}>
          <View style={s.avatar}>
            <Text style={s.avatarText}>{user?.name?.[0]?.toUpperCase() ?? '?'}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={s.profileName}>{user?.name ?? 'User'}</Text>
            <Text style={s.profileEmail}>{user?.email ?? ''}</Text>
          </View>
        </View>
        <TouchableOpacity style={s.logoutBtn} onPress={handleLogout}>
          <Text style={s.logoutBtnText}>Sign Out</Text>
        </TouchableOpacity>
      </View>

      {/* API URL */}
      <View style={s.card}>
        <Text style={s.sectionTitle}>— BACKEND CONNECTION —</Text>
        <Text style={s.helpText}>
          On a real device or phone via Wi-Fi, use your computer's local IP address:{'\n'}
          Current Wi-Fi IP: http://192.168.1.11:8000
        </Text>
        <View style={s.field}>
          <Text style={s.label}>API BASE URL</Text>
          <TextInput
            style={s.input}
            value={apiUrl}
            onChangeText={setApiUrl}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            placeholder="http://192.168.1.11:8000"
            placeholderTextColor={colors.textMuted}
          />
        </View>

        {/* Quick IP Presets */}
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginVertical: 4 }}>
          {[
            { label: 'Wi-Fi IP', icon: 'wifi', url: 'http://192.168.1.11:8000' },
            { label: 'Localhost', icon: 'desktop-outline', url: 'http://localhost:8000' },
            { label: 'Android Emulator', icon: 'phone-portrait-outline', url: 'http://10.0.2.2:8000' },
          ].map((preset) => {
            const isSelected = apiUrl === preset.url;
            return (
              <TouchableOpacity
                key={preset.url}
                style={{
                  backgroundColor: isSelected ? colors.primary : colors.bgElevated,
                  borderWidth: 1,
                  borderColor: isSelected ? colors.primaryDark : colors.borderMedium,
                  borderRadius: radius.xs,
                  paddingHorizontal: 8,
                  paddingVertical: 4,
                }}
                onPress={() => setApiUrl(preset.url)}
              >
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                  <Ionicons name={preset.icon} size={11} color={isSelected ? colors.white : colors.textSecondary} />
                  <Text
                    style={{
                      fontSize: 10,
                      fontWeight: '600',
                      color: isSelected ? colors.white : colors.textSecondary,
                    }}
                  >
                    {preset.label}
                  </Text>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        {health && (
          <View style={[s.healthBox, { borderColor: health.ok ? colors.emerald : colors.primary }]}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
              <Ionicons
                name={health.ok ? "checkmark-circle" : "close-circle"}
                size={13}
                color={health.ok ? colors.emerald : colors.primary}
              />
              <Text style={{ color: health.ok ? colors.emerald : colors.primary, fontSize: 12 }}>
                {health.msg}
              </Text>
            </View>
          </View>
        )}

        <View style={s.btnRow}>
          <TouchableOpacity style={[s.btn, s.btnOutline, { flex: 1 }]} onPress={testConnection}>
            <Text style={s.btnOutlineText}>Test Connection</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[s.btn, { flex: 1 }]} onPress={saveApiUrl} disabled={saving}>
            <Text style={s.btnText}>{saving ? 'Saving...' : 'Save URL'}</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* App info */}
      <View style={s.card}>
        <Text style={s.sectionTitle}>— APP INFO —</Text>
        {[
          ['Data Source', 'OpenStreetMap (Live)'],
          ['AI Provider', 'Rule-based (configurable)'],
          ['Auth', 'JWT Bearer Token'],
          ['Version', '2.0.0 (React Native)'],
        ].map(([lbl, val]) => (
          <View key={lbl} style={s.infoRow}>
            <Text style={s.infoLabel}>{lbl}</Text>
            <Text style={s.infoVal}>{val}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.bgPage },
  content: { padding: 12, gap: 10 },
  card: {
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderColor: colors.borderMedium,
    borderRadius: radius.xs,
    padding: 12,
    gap: 10,
    ...shadows.xs,
  },
  sectionTitle: {
    fontSize: 10, color: colors.textMuted, textAlign: 'center',
    letterSpacing: 1.2, textTransform: 'uppercase', fontStyle: 'italic',
  },
  profileRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  avatar: {
    width: 36, height: 36, borderRadius: radius.xs,
    backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center',
    ...shadows.xs,
  },
  avatarText: { color: colors.white, fontSize: 16, fontWeight: '700' },
  profileName: { fontSize: 14, fontWeight: '700', color: colors.textPrimary },
  profileEmail: { fontSize: 11, color: colors.textMuted, marginTop: 1 },
  logoutBtn: {
    borderWidth: 1, borderColor: colors.primary, borderRadius: radius.xs,
    paddingVertical: 7, alignItems: 'center',
  },
  logoutBtnText: { color: colors.primary, fontSize: 11, fontWeight: '700' },

  helpText: { fontSize: 11, color: colors.textMuted, fontStyle: 'italic', lineHeight: 18 },
  field: { gap: 5 },
  label: { fontSize: 10, color: colors.textMuted, letterSpacing: 0.9, textTransform: 'uppercase' },
  input: {
    backgroundColor: colors.bgPage,
    borderWidth: 1, borderBottomWidth: 2,
    borderColor: colors.borderSubtle, borderBottomColor: colors.borderDark,
    borderRadius: radius.xs, paddingHorizontal: 10, paddingVertical: 7,
    fontSize: 11, color: colors.textPrimary,
    fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace',
  },
  healthBox: {
    borderWidth: 1, borderRadius: radius.xs, padding: 10,
    backgroundColor: colors.bgPage,
  },
  btnRow: { flexDirection: 'row', gap: 8 },
  btn: {
    backgroundColor: colors.primary, borderRadius: radius.xs,
    paddingVertical: 8, alignItems: 'center',
    borderWidth: 1, borderColor: colors.borderDark, ...shadows.xs,
  },
  btnText: { color: colors.white, fontWeight: '700', fontSize: 11 },
  btnOutline: { backgroundColor: colors.bgElevated, borderColor: colors.borderDark },
  btnOutlineText: { color: colors.textPrimary, fontWeight: '700', fontSize: 11 },

  infoRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 5, borderBottomWidth: 1, borderBottomColor: colors.borderSubtle,
  },
  infoLabel: { fontSize: 11, color: colors.textMuted, fontWeight: '600' },
  infoVal: { fontSize: 11, color: colors.textPrimary },
});
