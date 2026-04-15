import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ChatHistoryProvider } from './contexts/ChatHistoryContext';
import Home from './pages/Home';
import _Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import EmailVerification from './pages/EmailVerification';
import AuthCallback from './pages/AuthCallback';
import Library from './pages/Library';
import VideoStudio from './pages/videoStudio';
import AudioCreator from './pages/audioCreator';
import CodeExecutor from './pages/CodeExecutor';
import Images from './pages/images';
import Documents from './pages/documents';
import MediaTools from './pages/mediaTools';
import Upload from './pages/Upload';
import Simone from './pages/simone';
import VideoTools from './pages/videoTools';
import ScriptSearchTools from './pages/scriptSearchTools';
import Chat from './pages/chat';
import Agents from './pages/agents';
import Users from './pages/Users';
import JobManagement from './pages/JobManagement';
import ApiKeys from './pages/ApiKeys';
import Settings from './pages/settings';
import Profile from './pages/Profile';
import SocialMediaTools from './pages/SocialMediaTools';
import Layout from './components/Layout';
import { Box, CircularProgress } from '@mui/material';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

const LoadingScreen: React.FC = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="100vh"
    bgcolor="background.default"
  >
    <CircularProgress size={60} />
  </Box>
);

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

const VideoRedirect: React.FC = () => {
  const { videoId } = useParams<{ videoId: string }>();
  return <Navigate to={`/dashboard/library/${videoId}`} replace />;
};

// Helper component for auth-guarded home page
const AuthGuardedHome: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Home />;
};

// Helper component for auth-guarded login page
const AuthGuardedLogin: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Landing Page */}
      <Route
        path="/"
        element={<AuthGuardedHome />}
      />

      {/* Login Route */}
      <Route
        path="/login"
        element={<AuthGuardedLogin />}
      />

      {/* Register Route */}
      <Route
        path="/register"
        element={<Register />}
      />

      {/* Email Verification Route */}
      <Route
        path="/verify-email"
        element={<EmailVerification />}
      />

      {/* OAuth Callback Route */}
      <Route
        path="/auth/callback"
        element={<AuthCallback />}
      />

      {/* Dashboard Routes - New hierarchical structure */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout>
              <Chat />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/library"
        element={
          <ProtectedRoute>
            <Layout>
              <Library />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/library/:videoId"
        element={
          <ProtectedRoute>
            <Layout>
              <Library />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/video-studio"
        element={
          <ProtectedRoute>
            <Layout>
              <VideoStudio />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/simone"
        element={
          <ProtectedRoute>
            <Layout>
              <Simone />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/audio"
        element={
          <Layout>
            <AudioCreator />
          </Layout>
        }
      />

      <Route
        path="/dashboard/code"
        element={
          <ProtectedRoute>
            <Layout>
              <CodeExecutor />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/images"
        element={
          <ProtectedRoute>
            <Layout>
              <Images />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/documents"
        element={
          <ProtectedRoute>
            <Layout>
              <Documents />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/media"
        element={
          <ProtectedRoute>
            <Layout>
              <MediaTools />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/upload"
        element={
          <ProtectedRoute>
            <Layout>
              <Upload />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/video-tools"
        element={
          <ProtectedRoute>
            <Layout>
              <VideoTools />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/script-search-tools"
        element={
          <ProtectedRoute>
            <Layout>
              <ScriptSearchTools />
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* /dashboard/chat redirects to /dashboard (chat is now the homepage) */}
      <Route path="/dashboard/chat" element={<Navigate to="/dashboard" replace />} />

      <Route
        path="/dashboard/agents"
        element={
          <ProtectedRoute>
            <Layout>
              <Agents />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/social-media"
        element={
          <ProtectedRoute>
            <Layout>
              <SocialMediaTools />
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* Speech Services is now a tab in Settings */}
      <Route path="/dashboard/speech-services" element={<Navigate to="/dashboard/settings" replace />} />

      <Route path="/dashboard/jobs" element={<Navigate to="/dashboard/admin/jobs" replace />} />

      <Route
        path="/dashboard/admin/jobs"
        element={
          <ProtectedRoute>
            <Layout>
              <JobManagement />
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* Admin Routes */}
      <Route
        path="/dashboard/admin/users"
        element={
          <ProtectedRoute>
            <Layout>
              <Users />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/admin/api-keys"
        element={
          <ProtectedRoute>
            <Layout>
              <ApiKeys />
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* API Keys for regular users (shows only their own keys) */}
      <Route
        path="/dashboard/api-keys"
        element={
          <ProtectedRoute>
            <Layout>
              <ApiKeys />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/admin/settings"
        element={
          <ProtectedRoute>
            <Layout>
              <Settings />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/settings"
        element={
          <ProtectedRoute>
            <Layout>
              <Settings />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/profile"
        element={
          <ProtectedRoute>
            <Layout>
              <Profile />
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* Legacy Route Redirects */}
      <Route path="/videos" element={<Navigate to="/dashboard/library" replace />} />
      <Route path="/library" element={<Navigate to="/dashboard/library" replace />} />
      <Route path="/video/:videoId" element={<VideoRedirect />} />
      <Route path="/jobs" element={<Navigate to="/dashboard/jobs" replace />} />
      <Route path="/users" element={<Navigate to="/dashboard/admin/users" replace />} />
      <Route path="/api-keys" element={<Navigate to="/dashboard/api-keys" replace />} />
      <Route path="/settings" element={<Navigate to="/dashboard/settings" replace />} />
      <Route path="/dashboard/ai-video-tools" element={<Navigate to="/dashboard/script-search-tools" replace />} />
      {/* Catch all route */}
      <Route
        path="*"
        element={<Navigate to="/dashboard" replace />}
      />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AuthProvider>
          <ChatHistoryProvider>
            <AppRoutes />
          </ChatHistoryProvider>
        </AuthProvider>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
