// src/hooks/useAutoScroll.ts
import { useEffect, useRef } from '@lynx-js/react';

export function useAutoScroll<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // scroll to bottom whenever children change
    // MutationObserver is robust for Lynx/React variations
    const obs = new MutationObserver(() => {
      el.scrollTop = el.scrollHeight;
    });
    obs.observe(el, { childList: true, subtree: true });
    return () => obs.disconnect();
  }, []);

  return ref;
}
