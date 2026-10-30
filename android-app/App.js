// Copyright (c) 2026 amthruster-dev. All rights reserved.
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, Pressable, ScrollView, Switch, Share, StyleSheet, StatusBar as RNStatusBar,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import AdMuter from './modules/ad-muter';

const EMPTY = { listener: false, enabled: true, muted: false, ads: 0, lastTitle: '', lastText: '' };

export default function App() {
  const [s, setS] = useState(EMPTY);
  const [log, setLog] = useState('');

  const refresh = useCallback(() => {
    try {
      setS(AdMuter.getStatus());
      setLog(AdMuter.getLog());
    } catch (e) {
      setLog('Error: ' + e.message);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 1000);
    return () => clearInterval(t);
  }, [refresh]);

  let label = 'Playing music';
  let color = '#1db954';
  if (!s.listener) { label = 'Access needed'; color = '#e8a400'; }
  else if (!s.enabled) { label = 'Stopped'; color = '#777777'; }
  else if (s.muted) { label = 'AD - MUTED'; color = '#e22134'; }
  else if (!s.lastTitle) { label = 'Waiting for Spoty'; color = '#777777'; }

  const logLines = log ? log.split('\n').slice(-80).reverse().join('\n') : 'No log yet.';

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <View style={[styles.banner, { backgroundColor: color }]}>
        <Text style={styles.bannerText}>{label}</Text>
      </View>

      <ScrollView contentContainerStyle={styles.body}>
        {!s.listener && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Allow notification access</Text>
            <Text style={styles.small}>
              The app reads Spoty's "now playing" notification to know when an ad plays.
            </Text>
            <Pressable style={styles.btn} onPress={() => AdMuter.openListenerSettings()}>
              <Text style={styles.btnText}>Open notification access</Text>
            </Pressable>
            <Text style={[styles.small, { marginTop: 10 }]}>
              If the switch is greyed out: open App info, tap the three dots, choose
              "Allow restricted settings", then try again.
            </Text>
            <Pressable style={[styles.btn, styles.btnAlt]} onPress={() => AdMuter.openAppSettings()}>
              <Text style={styles.btnText}>Open App info</Text>
            </Pressable>
          </View>
        )}

        <View style={styles.row}>
          <Text style={styles.label}>Mute ads</Text>
          <Switch value={s.enabled} onValueChange={(v) => { AdMuter.setEnabled(v); refresh(); }} />
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Ads muted</Text>
          <Text style={styles.value}>{s.ads}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Spoty shows</Text>
          <Text style={[styles.value, { flex: 1, textAlign: 'right' }]} numberOfLines={2}>
            {s.lastTitle ? `${s.lastTitle}${s.lastText ? '  |  ' + s.lastText : ''}` : '-'}
          </Text>
        </View>

        <View style={styles.btnRow}>
          <Pressable style={styles.btn} onPress={() => AdMuter.testMute()}>
            <Text style={styles.btnText}>Test mute</Text>
          </Pressable>
          <Pressable style={styles.btn} onPress={() => Share.share({ message: log || 'empty log' })}>
            <Text style={styles.btnText}>Share log</Text>
          </Pressable>
          <Pressable style={[styles.btn, styles.btnAlt]} onPress={() => { AdMuter.clearLog(); refresh(); }}>
            <Text style={styles.btnText}>Clear</Text>
          </Pressable>
        </View>

        <View style={styles.logBox}>
          <Text style={styles.logText}>{logLines}</Text>
        </View>
        <Text style={styles.footer}>© 2026 amthruster-dev. All rights reserved.</Text>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#121212', paddingTop: RNStatusBar.currentHeight || 24 },
  banner: { paddingVertical: 22, alignItems: 'center' },
  bannerText: { color: '#fff', fontSize: 26, fontWeight: '700' },
  body: { padding: 14 },
  card: { backgroundColor: '#1e1e1e', borderRadius: 10, padding: 14, marginBottom: 14 },
  cardTitle: { color: '#fff', fontSize: 16, fontWeight: '600', marginBottom: 6 },
  small: { color: '#bbbbbb', fontSize: 13 },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 8 },
  label: { color: '#999999', fontSize: 15 },
  value: { color: '#ffffff', fontSize: 15 },
  btnRow: { flexDirection: 'row', gap: 8, marginVertical: 10 },
  btn: { backgroundColor: '#2d6cdf', borderRadius: 8, paddingVertical: 11, paddingHorizontal: 12, marginTop: 8, alignItems: 'center' },
  btnAlt: { backgroundColor: '#444444' },
  btnText: { color: '#fff', fontWeight: '600' },
  logBox: { backgroundColor: '#1e1e1e', borderRadius: 8, padding: 10, minHeight: 200 },
  footer: { color: '#777777', fontSize: 11, textAlign: 'center', marginTop: 12 },
  logText: { color: '#dddddd', fontFamily: 'monospace', fontSize: 11 },
});
