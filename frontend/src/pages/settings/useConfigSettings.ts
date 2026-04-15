import { useState, useEffect, useCallback } from 'react';
import { directApi } from '../../utils/api';
import type { ConfigSetting } from './ConfigSettingField';

type CategoryConfig = Record<string, {
  label: string;
  settings: Record<string, ConfigSetting>;
}>;

export function useConfigSettings() {
  const [allConfig, setAllConfig] = useState<CategoryConfig>({});
  const [editValues, setEditValues] = useState<Record<string, string | number | boolean>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const result = await directApi.getConfigSettings();
    if (result.success && result.data) {
      setAllConfig(result.data);
      // Initialize edit values from current config
      const initial: Record<string, string | number | boolean> = {};
      for (const cat of Object.values(result.data)) {
        for (const [key, setting] of Object.entries(cat.settings)) {
          initial[key] = setting.value;
        }
      }
      setEditValues(initial);
    } else {
      setError(result.error || 'Failed to load config');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const setValue = useCallback((key: string, value: string | number | boolean) => {
    setEditValues(prev => ({ ...prev, [key]: value }));
  }, []);

  const saveCategory = useCallback(async (category: string) => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    const catConfig = allConfig[category];
    if (!catConfig) {
      setError('Category not found');
      setSaving(false);
      return;
    }

    // Only send settings that belong to this category
    const payload: Record<string, string | number | boolean> = {};
    for (const key of Object.keys(catConfig.settings)) {
      if (key in editValues) {
        payload[key] = editValues[key];
      }
    }

    const result = await directApi.updateConfigSettings(payload);
    if (result.success) {
      setSuccess(`Saved ${result.data?.count || 0} settings`);
      setTimeout(() => setSuccess(null), 3000);
      // Reload to get updated masked values
      await load();
    } else {
      setError(result.error || 'Failed to save');
    }
    setSaving(false);
  }, [allConfig, editValues, load]);

  const getSettingsForCategory = useCallback((category: string) => {
    return allConfig[category]?.settings || {};
  }, [allConfig]);

  return {
    allConfig,
    editValues,
    loading,
    saving,
    error,
    success,
    setValue,
    saveCategory,
    getSettingsForCategory,
    setError,
    setSuccess,
  };
}
