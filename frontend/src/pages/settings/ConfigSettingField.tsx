import React, { useState } from 'react';
import {
  Box,
  TextField,
  Switch,
  FormControlLabel,
  InputAdornment,
  IconButton,
  Chip,
  Typography,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  CheckCircleOutline,
} from '@mui/icons-material';

export interface ConfigSetting {
  value: string | number | boolean;
  configured: boolean;
  type: string;
  label: string;
  default: string | number | boolean;
  placeholder: string;
  provider?: string;
}

interface ConfigSettingFieldProps {
  settingKey: string;
  setting: ConfigSetting;
  value: string | number | boolean;
  onChange: (key: string, value: string | number | boolean) => void;
}

const ConfigSettingField: React.FC<ConfigSettingFieldProps> = ({
  settingKey,
  setting,
  value,
  onChange,
}) => {
  const [showPassword, setShowPassword] = useState(false);

  if (setting.type === 'boolean') {
    return (
      <FormControlLabel
        control={
          <Switch
            checked={Boolean(value)}
            onChange={(e) => onChange(settingKey, e.target.checked)}
          />
        }
        label={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2">{setting.label}</Typography>
            {setting.configured && (
              <Chip label="Set" size="small" color="success" variant="outlined" sx={{ height: 20, fontSize: '0.7rem' }} />
            )}
          </Box>
        }
      />
    );
  }

  return (
    <TextField
      fullWidth
      size="small"
      label={
        <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {setting.label}
          {setting.configured && (
            <CheckCircleOutline sx={{ fontSize: 14, color: 'success.main' }} />
          )}
        </Box>
      }
      type={setting.type === 'password' && !showPassword ? 'password' : setting.type === 'number' ? 'number' : 'text'}
      value={value ?? ''}
      onChange={(e) => {
        const val = setting.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value;
        onChange(settingKey, val);
      }}
      placeholder={String(setting.placeholder || setting.default || '')}
      InputProps={setting.type === 'password' ? {
        endAdornment: (
          <InputAdornment position="end">
            <IconButton size="small" onClick={() => setShowPassword(!showPassword)} edge="end">
              {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
            </IconButton>
          </InputAdornment>
        ),
      } : undefined}
    />
  );
};

export default ConfigSettingField;
