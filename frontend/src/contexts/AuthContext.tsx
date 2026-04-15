import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient, authApiClient } from '../utils/api';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  apiKey: string | null;
  userRole: 'admin' | 'user';
  // eslint-disable-next-line no-unused-vars
  login: (apiKeyOrUsername: string, password?: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
  // eslint-disable-next-line no-unused-vars
  setApiKey: (key: string, role?: 'admin' | 'user') => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [apiKey, setApiKeyState] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<'admin' | 'user'>('user');

  const setApiKey = (key: string, role: 'admin' | 'user' = 'user') => {
    setApiKeyState(key);
    setUserRole(role);
    localStorage.setItem('griot_api_key', key);
    localStorage.setItem('griot_user_role', role);
    // Update axios defaults
    apiClient.defaults.headers.common['X-API-Key'] = key;
    setIsAuthenticated(true);
  };

  const login = async (apiKeyOrUsername: string, password?: string): Promise<void> => {
    if (password) {
      // Username/password authentication
      try {
        const response = await authApiClient.post('/auth/login', {
          username: apiKeyOrUsername,
          password: password
        });

        if (response.data.success) {
          const returnedApiKey = response.data.api_key;
          if (!returnedApiKey) {
            throw new Error('No authentication token returned from server');
          }
          const userRole = response.data.role || 'user';
          setApiKey(returnedApiKey, userRole as 'admin' | 'user');
          return;
        } else {
          throw new Error(response.data.message || 'Login failed');
        }
      } catch (error: unknown) {
        const err = error as { response?: { data?: { detail?: string; message?: string } } };
        throw new Error(err.response?.data?.detail || err.response?.data?.message || 'Login failed');
      }
    } else {
      // API key authentication - use direct validation endpoint
      try {
        const validateResponse = await authApiClient.post('/auth/validate', undefined, {
          params: { api_key: apiKeyOrUsername }
        });

        if (validateResponse.data.valid || validateResponse.data.success) {
          // Direct API key validation successful
          const isAdminKey = apiKeyOrUsername.length > 50; // Assume longer keys are admin keys
          setApiKey(apiKeyOrUsername, isAdminKey ? 'admin' : 'user');
          return;
        } else {
          throw new Error('Invalid API key');
        }
      } catch (error: unknown) {
        const err = error as { response?: { status?: number; data?: { detail?: string; message?: string } } };
        if (err.response?.status === 401 || err.response?.status === 403) {
          throw new Error('Invalid API key');
        }
        const errorMessage = err.response?.data?.detail || err.response?.data?.message || 'Authentication failed';
        throw new Error(errorMessage);
      }
    }
  };

  const logout = () => {
    setApiKeyState(null);
    setUserRole('user');
    localStorage.removeItem('griot_api_key');
    localStorage.removeItem('griot_user_role');
    // Remove from axios defaults
    delete apiClient.defaults.headers.common['X-API-Key'];
    setIsAuthenticated(false);
  };

  const checkAuth = async (): Promise<boolean> => {
    const storedKey = localStorage.getItem('griot_api_key');
    const storedRole = localStorage.getItem('griot_user_role') as 'admin' | 'user' || 'user';

    if (!storedKey) {
      setIsLoading(false);
      return false;
    }

    // Check if this is a JWT token (starts with "eyJ")
    const isJwtToken = storedKey.startsWith('eyJ');

    if (isJwtToken) {
      // For JWT tokens, we can do basic validation locally
      try {
        // Decode JWT payload to check expiration (without verification)
        const payload = JSON.parse(atob(storedKey.split('.')[1]));
        const currentTime = Math.floor(Date.now() / 1000);

        if (payload.exp && payload.exp > currentTime) {
          // Token is not expired, consider it valid
          setApiKeyState(storedKey);
          setUserRole(storedRole);
          apiClient.defaults.headers.common['X-API-Key'] = storedKey;
          setIsAuthenticated(true);
          setIsLoading(false);
          return true;
        } else {
          // Token expired, remove it
          localStorage.removeItem('griot_api_key');
          localStorage.removeItem('griot_user_role');
          setIsLoading(false);
          return false;
        }
      } catch (error) {
        // Invalid JWT format, remove it
        console.error('Invalid JWT token format:', error);
        localStorage.removeItem('griot_api_key');
        localStorage.removeItem('griot_user_role');
        setIsLoading(false);
        return false;
      }
    } else {
      // For API keys, validate with server
      try {
        const validateResponse = await authApiClient.post('/auth/validate', undefined, {
          params: { api_key: storedKey }
        });

        if (validateResponse.data.valid || validateResponse.data.success) {
          setApiKeyState(storedKey);
          setUserRole(storedRole);
          apiClient.defaults.headers.common['X-API-Key'] = storedKey;
          setIsAuthenticated(true);
          return true;
        } else {
          localStorage.removeItem('griot_api_key');
          localStorage.removeItem('griot_user_role');
          return false;
        }
      } catch (error: unknown) {
        console.error('Auth check failed:', error);
        if (error instanceof Error && 'response' in error) {
          const axiosError = error as { response?: { status?: number } };
          if (axiosError.response?.status === 401 || axiosError.response?.status === 403) {
            localStorage.removeItem('griot_api_key');
            localStorage.removeItem('griot_user_role');
          }
        }
        return false;
      } finally {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    // Only validate stored JWT/API key — no auto-login
    checkAuth();
  }, []);

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    apiKey,
    userRole,
    login,
    logout,
    checkAuth,
    setApiKey,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};