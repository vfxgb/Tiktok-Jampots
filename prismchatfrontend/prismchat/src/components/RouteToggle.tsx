// src/components/RouteToggle.tsx
import type { RouteMode } from '../types/chat.js';

interface Props {
  mode: RouteMode;
  onChange(mode: RouteMode): void;
}

export default function RouteToggle({ mode, onChange }: Props) {
  const isPG = mode === 'prismguard';
  return (
    <view className="route-toggle">
      <view
        className={`toggle-seg ${!isPG ? 'active' : ''}`}
        bindtap={() => onChange('direct')}
      >
        <text>Direct</text>
      </view>
      <view
        className={`toggle-seg ${isPG ? 'active' : ''}`}
        bindtap={() => onChange('prismguard')}
      >
        <text>PrismGuard</text>
      </view>
    </view>
  );
}
