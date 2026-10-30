import { NativeModule, requireNativeModule } from 'expo';

export type AdStatus = {
  listener: boolean;
  enabled: boolean;
  muted: boolean;
  ads: number;
  lastTitle: string;
  lastText: string;
};

declare class AdMuterModule extends NativeModule<{}> {
  isListenerEnabled(): boolean;
  openListenerSettings(): void;
  openAppSettings(): void;
  getStatus(): AdStatus;
  setEnabled(enabled: boolean): void;
  getLog(): string;
  clearLog(): void;
  testMute(): void;
}

export default requireNativeModule<AdMuterModule>('AdMuter');
