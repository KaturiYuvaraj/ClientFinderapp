import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ActivityIndicator, KeyboardAvoidingView,
  Platform, ScrollView, StatusBar, Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from '../theme';
import { api } from '../services/api';

export default function LoginScreen({ onAuthSuccess, onShowToast }) {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [serverUrl, setServerUrl] = useState('');
  const [showServerConfig, setShowServerConfig] = useState(false);
  const [testingServer, setTestingServer] = useState(false);

  useEffect(() => {
    api.getBaseUrl().then(setServerUrl);
  }, []);

  const handleSaveServer = async () => {
    setTestingServer(true);
    try {
      await api.setBaseUrl(serverUrl.trim());
      const res = await api.checkHealth();
      onShowToast(`Backend Connected: ${res?.status || res?.message || 'OK'}`, 'success');
      setShowServerConfig(false);
    } catch (err) {
      onShowToast(`Cannot reach server: ${err.message}`, 'error');
    } finally {
      setTestingServer(false);
    }
  };

  const handleSubmit = async () => {
    if (!email.trim() || !password.trim()) {
      onShowToast('Please fill in all fields.', 'error');
      return;
    }
    setLoading(true);
    try {
      if (isRegister) {
        if (!name.trim()) throw new Error('Please enter your name.');
        const res = await api.register(name, email, password);
        onShowToast(`Welcome, ${res.user.name}!`, 'success');
        onAuthSuccess(res.user);
      } else {
        const res = await api.login(email, password);
        onShowToast(`Welcome back, ${res.user.name}!`, 'success');
        onAuthSuccess(res.user);
      }
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = () => {
    setName('Yuvaraj Agency');
    setEmail('yuvaraj@agency.com');
    setPassword('password123');
    onShowToast('Demo credentials filled!', 'info');
  };

  return (
    <KeyboardAvoidingView
      style={s.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={s.container} keyboardShouldPersistTaps="handled">
        {/* Brand */}
        <View style={s.brand}>
          <Image
            source={require('../../assets/app-logo.png')}
            style={s.appLogoImage}
            resizeMode="contain"
          />
          <Text style={s.appName}>AI Client Finder</Text>
          <Text style={s.tagline}>
            Identify high-probability business leads from live data with AI scoring.
          </Text>
        </View>

        {/* Card */}
        <View style={s.card}>
          <View style={s.topStripe} />

          {/* Tab toggle */}
          <View style={s.tabRow}>
            <TouchableOpacity
              style={[s.tab, !isRegister && s.tabActive]}
              onPress={() => setIsRegister(false)}
            >
              <Text style={[s.tabText, !isRegister && s.tabTextActive]}>Sign In</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[s.tab, isRegister && s.tabActive]}
              onPress={() => setIsRegister(true)}
            >
              <Text style={[s.tabText, isRegister && s.tabTextActive]}>Create Account</Text>
            </TouchableOpacity>
          </View>

          {/* Fields */}
          {isRegister && (
            <View style={s.formGroup}>
              <Text style={s.label}>FULL NAME OR AGENCY</Text>
              <TextInput
                style={s.input}
                placeholder="e.g. Apex Digital Studios"
                placeholderTextColor={colors.textMuted}
                value={name}
                onChangeText={setName}
                autoCapitalize="words"
              />
            </View>
          )}

          <View style={s.formGroup}>
            <Text style={s.label}>EMAIL ADDRESS</Text>
            <TextInput
              style={s.input}
              placeholder="you@agency.com"
              placeholderTextColor={colors.textMuted}
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
            />
          </View>

          <View style={s.formGroup}>
            <Text style={s.label}>PASSWORD</Text>
            <TextInput
              style={s.input}
              placeholder="••••••••"
              placeholderTextColor={colors.textMuted}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />
          </View>

          <TouchableOpacity
            style={[s.btn, loading && s.btnDisabled]}
            onPress={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color={colors.white} size="small" />
            ) : (
              <Text style={s.btnText}>
                {isRegister ? 'Register & Access Leads →' : 'Sign In to Workspace →'}
              </Text>
            )}
          </TouchableOpacity>

          {/* Demo fill */}
          <View style={s.demoRow}>
            <Text style={s.demoHint}>Testing local backend?</Text>
            <TouchableOpacity style={s.demoBtn} onPress={fillDemo}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Ionicons name="sparkles" size={12} color={colors.primary} />
                <Text style={s.demoBtnText}>Fill Demo Account</Text>
              </View>
            </TouchableOpacity>
          </View>

          {/* Server Config Row */}
          <View style={s.serverRow}>
            <TouchableOpacity
              style={s.serverToggle}
              onPress={() => setShowServerConfig(!showServerConfig)}
            >
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                <Ionicons name="server-outline" size={13} color={colors.textSecondary} />
                <Text style={s.serverToggleText}>
                  Server: <Text style={{ color: colors.primary, fontWeight: '700' }}>{serverUrl || '...'}</Text>
                </Text>
                <Ionicons name={showServerConfig ? "chevron-up" : "chevron-down"} size={12} color={colors.textSecondary} />
              </View>
            </TouchableOpacity>

            {showServerConfig && (
              <View style={s.serverBox}>
                <Text style={s.serverHint}>
                  For physical mobile devices, use your PC's Wi-Fi IP (192.168.1.11:8000):
                </Text>
                <TextInput
                  style={s.serverInput}
                  value={serverUrl}
                  onChangeText={setServerUrl}
                  autoCapitalize="none"
                  autoCorrect={false}
                  placeholder="http://192.168.1.11:8000"
                  placeholderTextColor={colors.textMuted}
                />
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginVertical: 4 }}>
                  {[
                    { label: 'Wi-Fi IP', icon: 'wifi', url: 'http://192.168.1.11:8000' },
                    { label: 'Localhost', icon: 'desktop-outline', url: 'http://localhost:8000' },
                    { label: 'Android Loopback', icon: 'phone-portrait-outline', url: 'http://10.0.2.2:8000' },
                  ].map((p) => {
                    const isSelected = serverUrl === p.url;
                    return (
                      <TouchableOpacity
                        key={p.url}
                        style={[s.presetChip, isSelected && s.presetChipActive]}
                        onPress={() => setServerUrl(p.url)}
                      >
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                          <Ionicons name={p.icon} size={10} color={isSelected ? colors.white : colors.textSecondary} />
                          <Text style={[s.presetChipText, isSelected && s.presetChipTextActive]}>
                            {p.label}
                          </Text>
                        </View>
                      </TouchableOpacity>
                    );
                  })}
                </View>
                <TouchableOpacity
                  style={[s.serverSaveBtn, testingServer && { opacity: 0.6 }]}
                  onPress={handleSaveServer}
                  disabled={testingServer}
                >
                  <Text style={s.serverSaveText}>
                    {testingServer ? 'Testing Connection...' : '✓ Save & Test Connection'}
                  </Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>

        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
          <Ionicons name="shield-checkmark-outline" size={12} color={colors.textMuted} />
          <Text style={s.footer}>JWT Authenticated · Ethical Public Data Engine</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bgPage },
  container: {
    padding: 16,
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 24) + 20 : 30,
    alignItems: 'center',
    gap: 12,
  },
  brand: { alignItems: 'center', gap: 4, marginBottom: 2 },
  appLogoImage: {
    width: 72,
    height: 72,
    borderRadius: radius.md,
    marginBottom: 4,
    ...shadows.sm,
  },
  appName: {
    fontSize: 17,
    fontWeight: '700',
    color: colors.textPrimary,
    letterSpacing: -0.3,
  },
  tagline: {
    fontSize: 10,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 14,
    maxWidth: 280,
    fontStyle: 'italic',
  },
  card: {
    width: '100%',
    backgroundColor: colors.bgCard,
    borderWidth: 2,
    borderColor: colors.borderDark,
    borderRadius: radius.sm,
    padding: 14,
    gap: 10,
    ...shadows.sm,
    overflow: 'hidden',
  },
  topStripe: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
    backgroundColor: colors.primary,
  },
  tabRow: {
    flexDirection: 'row',
    backgroundColor: colors.bgElevated,
    borderRadius: radius.xs,
    padding: 3,
    borderWidth: 1,
    borderColor: colors.borderSubtle,
    marginTop: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 6,
    alignItems: 'center',
    borderRadius: radius.xs,
  },
  tabActive: {
    backgroundColor: colors.primary,
    ...shadows.xs,
  },
  tabText: { fontSize: 12, color: colors.textMuted, fontWeight: '600', letterSpacing: 0.3 },
  tabTextActive: { color: colors.white },
  formGroup: { gap: 5 },
  label: {
    fontSize: 10,
    letterSpacing: 0.9,
    color: colors.textMuted,
    fontWeight: '400',
    textTransform: 'uppercase',
  },
  input: {
    backgroundColor: colors.bgPage,
    borderWidth: 1,
    borderColor: colors.borderMedium,
    borderRadius: radius.xs,
    paddingHorizontal: 10,
    paddingVertical: 7,
    fontSize: 12,
    color: colors.textPrimary,
    fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace',
  },
  btn: {
    backgroundColor: colors.primary,
    borderRadius: radius.xs,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colors.borderDark,
    ...shadows.sm,
    marginTop: 2,
  },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: colors.white, fontSize: 12, fontWeight: '700', letterSpacing: 0.3 },
  demoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
    paddingTop: 12,
  },
  demoHint: { fontSize: 11, color: colors.textMuted, fontStyle: 'italic' },
  demoBtn: {
    borderWidth: 1,
    borderColor: colors.borderMedium,
    borderRadius: radius.xs,
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: colors.bgElevated,
  },
  demoBtnText: { fontSize: 11, color: colors.primary, fontWeight: '600' },
  serverRow: {
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
    paddingTop: 10,
  },
  serverToggle: {
    alignItems: 'center',
    paddingVertical: 4,
  },
  serverToggleText: {
    fontSize: 11,
    color: colors.textSecondary,
    fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace',
  },
  serverBox: {
    marginTop: 8,
    backgroundColor: colors.bgElevated,
    borderRadius: radius.xs,
    padding: 10,
    borderWidth: 1,
    borderColor: colors.borderMedium,
    gap: 6,
  },
  serverHint: {
    fontSize: 10,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  serverInput: {
    backgroundColor: colors.bgPage,
    borderWidth: 1,
    borderColor: colors.borderMedium,
    borderRadius: radius.xs,
    paddingHorizontal: 10,
    paddingVertical: 6,
    fontSize: 12,
    color: colors.textPrimary,
    fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace',
  },
  presetChip: {
    backgroundColor: colors.bgPage,
    borderWidth: 1,
    borderColor: colors.borderMedium,
    borderRadius: radius.xs,
    paddingHorizontal: 7,
    paddingVertical: 3,
  },
  presetChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primaryDark,
  },
  presetChipText: {
    fontSize: 9,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  presetChipTextActive: {
    color: colors.white,
  },
  serverSaveBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.xs,
    paddingVertical: 8,
    alignItems: 'center',
    marginTop: 4,
    borderWidth: 1,
    borderColor: colors.borderDark,
  },
  serverSaveText: {
    color: colors.white,
    fontSize: 11,
    fontWeight: '700',
  },
  footer: { fontSize: 11, color: colors.textMuted, textAlign: 'center', fontStyle: 'italic' },
});
