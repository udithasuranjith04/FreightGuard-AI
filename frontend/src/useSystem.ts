import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";
import type { Health, ModelInfo } from "./api";
export interface SystemState {
  health: Health | null;
  info: ModelInfo | null;
  healthError: string | null;
  infoError: string | null;
  loading: boolean;
  checkedAt: Date | null;
}
const initial: SystemState = {
  health: null,
  info: null,
  healthError: null,
  infoError: null,
  loading: true,
  checkedAt: null,
};
export function useSystem() {
  const [state, setState] = useState<SystemState>(initial);
  const sequence = useRef(0);
  const refresh = useCallback(async () => {
    const id = ++sequence.current;
    setState({ ...initial, loading: true });
    const [health, info] = await Promise.allSettled([api.health(), api.info()]);
    if (id !== sequence.current) return;
    const message = (reason: unknown) =>
      reason instanceof ApiError ? reason.message : "The status check failed.";
    setState({
      health: health.status === "fulfilled" ? health.value : null,
      info: info.status === "fulfilled" ? info.value : null,
      healthError: health.status === "rejected" ? message(health.reason) : null,
      infoError: info.status === "rejected" ? message(info.reason) : null,
      loading: false,
      checkedAt: new Date(),
    });
  }, []);
  useEffect(() => {
    const firstCheck = window.setTimeout(() => {
      void refresh();
    }, 0);
    const timer = window.setInterval(() => {
      void refresh();
    }, 60000);
    const invalidate = () => {
      ++sequence.current;
    };
    return () => {
      invalidate();
      window.clearTimeout(firstCheck);
      window.clearInterval(timer);
    };
  }, [refresh]);
  return { ...state, refresh };
}
