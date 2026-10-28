import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  StatusBar, Animated, Platform, Dimensions, Image,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { api } from './src/services/api';
import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import SearchScreen from './src/screens/SearchScreen';
import LeadsScreen from './src/screens/LeadsScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { colors, radius, shadows } from './src/theme';
import { Ionicons } from '@expo/vector-icons';

const TABS = [
  { key: 'dashboard', label: 'Dashboard', icon: 'stats-chart-outline', iconActive: 'stats-chart' },
  { key: 'search',    label: 'Search',    icon: 'search-outline',      iconActive: 'search' },
  { key: 'leads',     label: 'Leads',     icon: 'folder-open-outline', iconActive: 'folder-open' },
  { key: 'settings',  label: 'Settings',  icon: 'settings-outline',    iconActive: 'settings' },
];

const TOAST_BG = {
  success: colors.emeraldLight,
  error:   colors.primaryLight,
  info:    colors.cyanLight,
};
const TOAST_BORDER = {
  success: colors.emerald,
  error:   colors.primary,
  info:    colors.cyan,
};

// On web, simulate a phone viewport; on native, take full screen
const IS_WEB = Platform.OS === 'web';
const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');
const PHONE_W = IS_WEB ? Math.min(390, SCREEN_W) : SCREEN_W;
const PHONE_H = IS_WEB ? Math.min(844, SCREEN_H - 40) : SCREEN_H;

function Toast({ msg, type, visible }) {
  const anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: 200, useNativeDriver: true }),
        Animated.delay(2400),
        Animated.timing(anim, { toValue: 0, duration: 200, useNativeDriver: true }),
      ]).start();
    }
  }, [visible, msg]);

  return (
    <Animated.View
      style={[
        ts.toast,
        { backgroundColor: TOAST_BG[type] || colors.bgCard, borderLeftColor: TOAST_BORDER[type] || colors.borderDark },
        { opacity: anim, transform: [{ translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) }] },
      ]}
      pointerEvents="none"
    >
      <Text style={ts.toastText}>{msg}</Text>
    </Animated.View>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [toast, setToast] = useState({ msg: '', type: 'info', visible: false });

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const token = await api.init();
        if (token) {
          const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('timeout')), 2000)
          );
          const me = await Promise.race([api.getMe(), timeoutPromise]);
          if (active && me) setUser(me);
        }
      } catch (_) {
        // Token invalid or server unreachable quickly - fall through to login screen
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type, visible: true });
    setTimeout(() => setToast((t) => ({ ...t, visible: false })), 3000);
  };

  const handleAuthSuccess = (u) => { setUser(u); setActiveTab('dashboard'); };
  const handleLogout = () => { setUser(null); setActiveTab('dashboard'); };

  const inner = (() => {
    if (loading) {
      return (
        <View style={s.splash}>
          <Image source={require('./assets/app-logo.png')} style={s.splashLogo} resizeMode="contain" />
          <Text style={s.splashTitle}>AI Client Finder</Text>
          <Text style={s.splashSub}>Loading...</Text>
        </View>
      );
    }

    if (!user) {
      return (
        <>
          <StatusBar barStyle="dark-content" backgroundColor={colors.bgPage} />
          <LoginScreen onAuthSuccess={handleAuthSuccess} onShowToast={showToast} />
          <Toast msg={toast.msg} type={toast.type} visible={toast.visible} />
        </>
      );
    }

    const renderScreen = () => {
      switch (activeTab) {
        case 'dashboard': return <DashboardScreen user={user} onShowToast={showToast} />;
        case 'search':    return <SearchScreen onShowToast={showToast} />;
        case 'leads':     return <LeadsScreen onShowToast={showToast} />;
        case 'settings':  return <SettingsScreen user={user} onLogout={handleLogout} onShowToast={showToast} />;
        default:          return null;
      }
    };

    return (
      <>
        <StatusBar barStyle="dark-content" backgroundColor={colors.bgElevated} />
        {/* Top Header */}
        <View style={s.topBar}>
          <View style={s.logoRow}>
            <Image source={require('./assets/app-logo.png')} style={s.topLogo} resizeMode="contain" />
            <View>
              <Text style={s.appName}>AI Client Finder</Text>
              <Text style={s.appSub}>{TABS.find((t) => t.key === activeTab)?.label ?? ''}</Text>
            </View>
          </View>
          <View style={s.userBadge}>
            <Text style={s.userInitial}>{user.name?.[0]?.toUpperCase() ?? '?'}</Text>
          </View>
        </View>

        {/* Screen */}
        <View style={s.screenWrap}>{renderScreen()}</View>

        {/* Bottom Tab Bar */}
        <View style={s.tabBar}>
          {TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <TouchableOpacity
                key={tab.key}
                style={[s.tabItem, isActive && s.tabItemActive]}
                onPress={() => setActiveTab(tab.key)}
              >
                <Ionicons
                  name={isActive ? tab.iconActive : tab.icon}
                  size={19}
                  color={isActive ? colors.primary : colors.textMuted}
                />
                <Text style={[s.tabLabel, isActive && s.tabLabelActive]}>
                  {tab.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <Toast msg={toast.msg} type={toast.type} visible={toast.visible} />
      </>
    );
  })();

  // On web: wrap in a centered phone frame; on native: full screen
  if (IS_WEB) {
    return (
      <SafeAreaProvider>
        <View style={s.webRoot}>
          <View style={[s.phoneFrame, { width: PHONE_W, height: PHONE_H }]}>
            <SafeAreaView style={s.page}>
              {inner}
            </SafeAreaView>
          </View>
        </View>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={s.page}>{inner}</SafeAreaView>
    </SafeAreaProvider>
  );
}

const s = StyleSheet.create({
  // Web outer wrapper — centers the phone frame
  webRoot: {
    flex: 1,
    backgroundColor: '#d4c9b8',
    alignItems: 'center',
    justifyContent: 'center',
  },
  phoneFrame: {
    backgroundColor: colors.bgPage,
    borderRadius: IS_WEB ? 20 : 0,
    overflow: 'hidden',
    borderWidth: IS_WEB ? 2 : 0,
    borderColor: colors.borderDark,
    ...(IS_WEB ? {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.3,
      shadowRadius: 24,
    } : {}),
  },

  page: { flex: 1, backgroundColor: colors.bgPage },

  // Splash
  splash: { flex: 1, backgroundColor: colors.bgPage, alignItems: 'center', justifyContent: 'center', gap: 8 },
  splashLogo: { width: 88, height: 88, borderRadius: radius.md, marginBottom: 8 },
  splashTitle: { fontSize: 20, fontWeight: '700', color: colors.textPrimary },
  splashSub: { fontSize: 12, color: colors.textMuted, fontStyle: 'italic' },

  // Top bar — compact & safe from Android status bar
  topBar: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: colors.bgElevated,
    paddingHorizontal: 14,
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 24) + 8 : 10,
    paddingBottom: 10,
    borderBottomWidth: 2, borderBottomColor: colors.borderDark,
    ...shadows.xs,
  },
  logoRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  topLogo: { width: 32, height: 32, borderRadius: radius.xs },
  appName: { fontSize: 14, fontWeight: '700', color: colors.textPrimary, letterSpacing: -0.2 },
  appSub: { fontSize: 9, color: colors.textMuted, letterSpacing: 0.5, textTransform: 'uppercase' },
  userBadge: {
    width: 30, height: 30, borderRadius: radius.xs,
    backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center',
    borderWidth: 2, borderColor: colors.borderDark,
  },
  userInitial: { color: colors.white, fontWeight: '700', fontSize: 13 },

  screenWrap: { flex: 1 },

  // Bottom tab bar — comfortable spacing above Android gesture pill / iOS home bar
  tabBar: {
    flexDirection: 'row',
    backgroundColor: colors.bgElevated,
    borderTopWidth: 2,
    borderTopColor: colors.borderDark,
    paddingBottom: Platform.OS === 'ios' ? 24 : 16,
    paddingTop: 6,
    ...shadows.sm,
  },
  tabItem: {
    flex: 1, alignItems: 'center', gap: 3,
    paddingTop: 4, paddingBottom: 4,
    borderTopWidth: 2, borderTopColor: 'transparent',
  },
  tabItemActive: {
    borderTopColor: colors.primary,
    backgroundColor: colors.bgCard,
  },
  tabIcon: { fontSize: 18 },
  tabLabel: { fontSize: 10, color: colors.textMuted, letterSpacing: 0.3, fontWeight: '500' },
  tabLabelActive: { color: colors.primary, fontWeight: '700' },
});

// Toast styles
const ts = StyleSheet.create({
  toast: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 100 : 80,
    left: 12, right: 12,
    padding: 10,
    borderRadius: radius.xs,
    borderWidth: 1,
    borderColor: colors.borderDark,
    borderLeftWidth: 4,
    ...shadows.md,
    zIndex: 9999,
  },
  toastText: { fontSize: 12, color: colors.textPrimary, fontWeight: '500' },
});
