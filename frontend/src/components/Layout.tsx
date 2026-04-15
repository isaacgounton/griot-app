import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  Toolbar,
  Typography,
  Button,
  ThemeProvider,
  createTheme,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useMediaQuery,
  Collapse,
  Tooltip,
  Badge,
  PaletteMode
} from '@mui/material';
import {
  VideoLibrary,
  List as ListIcon,
  Logout,
  Person,
  Settings,
  MenuBook,
  Dashboard as _DashboardIcon,
  People as UsersIcon,
  Work as JobsIcon,
  VpnKey as ApiKeyIcon,
  Menu as MenuIcon,
  ChevronLeft,
  ExpandLess,
  ExpandMore,
  AdminPanelSettings,
  VolumeUp as AudioIcon,
  Code as CodeIcon,
  Description as DocumentIcon,
  Image as ImageIcon,
  Storage as MediaIcon,
  SmartToy as SimoneIcon,
  AutoAwesome as ScriptIcon,
  Chat as ChatIcon,
  SmartToy as AgentIcon,
  Share as ShareIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  MovieCreation as VideoStudioIcon,
  EditNote as ResearchIcon,
  Handyman as UtilitiesIcon,
  Movie as VideoToolsIcon
} from '@mui/icons-material';

interface LayoutProps {
  children: React.ReactNode;
}

const DRAWER_WIDTH = 280;
const DRAWER_WIDTH_COLLAPSED = 76;

const getDesignTokens = (mode: PaletteMode) => {
  const isDark = mode === 'dark';
  const backgroundDefault = isDark ? '#0f172a' : '#f8fafc';
  const backgroundPaper = isDark ? '#1e293b' : '#ffffff';
  const textPrimary = isDark ? '#e2e8f0' : '#1a202c';
  const borderColor = isDark ? '#334155' : '#e2e8f0';
  const hoverColor = isDark ? 'rgba(148, 163, 184, 0.12)' : '#f1f5f9';
  const parentActiveBg = isDark ? 'rgba(56, 189, 248, 0.16)' : '#e0f2fe';
  const parentActiveHover = isDark ? 'rgba(56, 189, 248, 0.24)' : '#b3e5fc';
  const parentActiveColor = isDark ? '#38bdf8' : '#0369a1';
  const parentActiveBorder = isDark ? '#38bdf8' : '#0ea5e9';

  return {
    palette: {
      mode,
      primary: {
        main: '#1976d2',
        light: '#42a5f5',
        dark: '#1565c0',
      },
      secondary: {
        main: '#f50057',
        light: '#ff5983',
        dark: '#c51162',
      },
      background: {
        default: backgroundDefault,
        paper: backgroundPaper,
      },
      grey: {
        50: '#fafafa',
        100: '#f5f5f5',
        200: '#eeeeee',
        300: '#e0e0e0',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h4: {
        fontWeight: 700,
      },
      h5: {
        fontWeight: 600,
      },
      h6: {
        fontWeight: 600,
      },
    },
    components: {
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
            backgroundColor: backgroundPaper,
            color: textPrimary,
            borderBottom: `1px solid ${borderColor}`,
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRight: `1px solid ${borderColor}`,
            backgroundColor: backgroundPaper,
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            margin: '2px 8px',
            transition: 'all 0.2s ease-in-out',
            '&.Mui-selected': {
              // Default active state (bright blue for child pages)
              backgroundColor: '#3b82f6',
              color: '#ffffff',
              '& .MuiListItemIcon-root': {
                color: '#ffffff',
              },
              '&:hover': {
                backgroundColor: '#2563eb',
              },
            },
            '&.parent-active': {
              // Parent active state (subtle blue for dashboard when child is active)
              backgroundColor: parentActiveBg,
              color: parentActiveColor,
              borderLeft: `3px solid ${parentActiveBorder}`,
              borderTopRightRadius: 8,
              borderBottomRightRadius: 8,
              '& .MuiListItemIcon-root': {
                color: parentActiveColor,
              },
              '&:hover': {
                backgroundColor: parentActiveHover,
              },
            },
            '&:hover': {
              backgroundColor: hoverColor,
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none' as const,
            fontWeight: 500,
            borderRadius: 8,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
          },
        },
      },
    },
  };
};

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path?: string;
  children?: NavItem[];
  badge?: number;
  adminOnly?: boolean;
  sectionHeader?: boolean;
  dividerBefore?: boolean;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const getInitialMode = (): PaletteMode => {
    if (typeof window === 'undefined') {
      return 'light';
    }
    const stored = localStorage.getItem('theme');
    if (stored === 'light' || stored === 'dark') {
      return stored;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };

  const [colorMode, setColorMode] = useState<PaletteMode>(getInitialMode());
  const muiTheme = useMemo(() => createTheme(getDesignTokens(colorMode)), [colorMode]);

  const navigate = useNavigate();
  const location = useLocation();
  const { logout, apiKey, userRole } = useAuth();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('lg'));

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', colorMode);
    }
    document.documentElement.setAttribute('data-theme', colorMode);
  }, [colorMode]);

  const toggleColorMode = useCallback(() => {
    setColorMode(prev => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleToggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => undefined);
    } else if (document.exitFullscreen) {
      document.exitFullscreen().catch(() => undefined);
    }
  }, []);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [expandedItems, setExpandedItems] = useState<string[]>(['management']);

  // Cleanup menu anchor on unmount to prevent MUI warnings
  useEffect(() => {
    return () => {
      setAnchorEl(null);
    };
  }, []);

  const navigationItems: NavItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <ChatIcon />,
      path: '/dashboard'
    },
    {
      id: 'agents',
      label: 'AI Agents',
      icon: <AgentIcon />,
      path: '/dashboard/agents'
    },
    // --- Research & Writing section ---
    {
      id: 'section-research',
      label: 'Research & Writing',
      icon: <ResearchIcon />,
      sectionHeader: true,
      dividerBefore: true
    },
    {
      id: 'script-search-tools',
      label: 'Script & Research',
      icon: <ScriptIcon />,
      path: '/dashboard/script-search-tools'
    },
    {
      id: 'simone',
      label: 'Simone AI',
      icon: <SimoneIcon />,
      path: '/dashboard/simone'
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <DocumentIcon />,
      path: '/dashboard/documents'
    },
    // --- Create section ---
    {
      id: 'section-create',
      label: 'Create',
      icon: <VideoStudioIcon />,
      sectionHeader: true,
      dividerBefore: true
    },
    {
      id: 'video-studio',
      label: 'Video Studio',
      icon: <VideoLibrary />,
      path: '/dashboard/video-studio'
    },
    {
      id: 'audio',
      label: 'Audio & Speech',
      icon: <AudioIcon />,
      path: '/dashboard/audio'
    },
    {
      id: 'images',
      label: 'Image Generation',
      icon: <ImageIcon />,
      path: '/dashboard/images'
    },
    // --- Utilities section ---
    {
      id: 'section-utilities',
      label: 'Utilities',
      icon: <UtilitiesIcon />,
      sectionHeader: true,
      dividerBefore: true
    },
    {
      id: 'video-tools',
      label: 'Video Tools',
      icon: <VideoToolsIcon />,
      path: '/dashboard/video-tools'
    },
    {
      id: 'media',
      label: 'Media Tools',
      icon: <MediaIcon />,
      path: '/dashboard/media'
    },
    {
      id: 'code',
      label: 'Code Executor',
      icon: <CodeIcon />,
      path: '/dashboard/code'
    },
    {
      id: 'social-media',
      label: 'Social Media',
      icon: <ShareIcon />,
      path: '/dashboard/social-media'
    },
    // --- Bottom section ---
    {
      id: 'library',
      label: 'Library',
      icon: <ListIcon />,
      path: '/dashboard/library',
      dividerBefore: true
    },
    {
      id: 'api-keys',
      label: 'API Keys',
      icon: <ApiKeyIcon />,
      path: '/dashboard/api-keys'
    },
    {
      id: 'management',
      label: 'Admin',
      icon: <AdminPanelSettings />,
      adminOnly: true,
      dividerBefore: true,
      children: [
        {
          id: 'jobs',
          label: 'Jobs & Cleanup',
          icon: <JobsIcon />,
          path: '/dashboard/admin/jobs',
          badge: 3,
          adminOnly: true
        },
        {
          id: 'users',
          label: 'Users',
          icon: <UsersIcon />,
          path: '/dashboard/admin/users',
          adminOnly: true
        },
        {
          id: 'admin-settings',
          label: 'Settings',
          icon: <Settings />,
          path: '/dashboard/admin/settings',
          adminOnly: true
        }
      ]
    }
  ];

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleSidebarToggle = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleProfileMenuClose();
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const handleExpandToggle = (itemId: string) => {
    setExpandedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const isActive = (path: string) => {
    // Exact match for dashboard to avoid conflicts
    if (path === '/dashboard' && location.pathname === '/dashboard') return true;
    // For other paths, check if current path starts with the nav path
    if (path !== '/dashboard' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const isParentActive = (item: NavItem) => {
    // Check if any child is active (for parent highlighting)
    if (!item.children) return false;
    return item.children.some(child => child.path && isActive(child.path));
  };

  const maskedApiKey = apiKey ? `${apiKey.substring(0, 8)}...` : '';

  const filterNavItems = (items: NavItem[]): NavItem[] => {
    return items.filter(item => {
      // Filter out admin-only items for non-admin users
      if (item.adminOnly && userRole !== 'admin') {
        return false;
      }

      // Recursively filter children
      if (item.children) {
        const filteredChildren = filterNavItems(item.children);
        // If a parent has children but all are filtered out, hide the parent too
        if (filteredChildren.length === 0) {
          return false;
        }
        // Update the item with filtered children
        item.children = filteredChildren;
      }

      return true;
    });
  };

  const filteredNavigationItems = filterNavItems([...navigationItems]);

  const renderNavItem = (item: NavItem, level: number = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.id);
    const active = item.path ? isActive(item.path) : false;
    const parentActiveState = hasChildren ? isParentActive(item) : false;

    const divider = item.dividerBefore ? (
      <Divider key={`divider-${item.id}`} sx={{ my: 1, mx: 2 }} />
    ) : null;

    // Section header rendering
    if (item.sectionHeader) {
      if (sidebarCollapsed) {
        return (
          <React.Fragment key={item.id}>
            {divider}
            <Divider key={`sh-divider-${item.id}`} sx={{ my: 1, mx: 2 }} />
          </React.Fragment>
        );
      }
      return (
        <React.Fragment key={item.id}>
          {divider}
          <Typography
            variant="overline"
            sx={{
              px: 3,
              pt: 1.5,
              pb: 0.5,
              display: 'block',
              color: 'text.secondary',
              fontSize: '0.7rem',
              fontWeight: 700,
              letterSpacing: '0.08em'
            }}
          >
            {item.label}
          </Typography>
        </React.Fragment>
      );
    }

    if (hasChildren) {
      return (
        <React.Fragment key={item.id}>
          {divider}
          <ListItem disablePadding>
            <ListItemButton
              onClick={() => handleExpandToggle(item.id)}
              className={parentActiveState ? 'parent-active' : ''}
              sx={{
                pl: sidebarCollapsed ? 0 : level * 2 + 2,
                minHeight: 44,
                justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                px: sidebarCollapsed ? 1 : undefined,
              }}
            >
              <ListItemIcon sx={{ minWidth: sidebarCollapsed ? 0 : 40, justifyContent: 'center' }}>
                {item.icon}
              </ListItemIcon>
              {!sidebarCollapsed && (
                <>
                  <ListItemText
                    primary={item.label}
                    primaryTypographyProps={{
                      fontSize: '0.875rem',
                      fontWeight: parentActiveState ? 600 : 500
                    }}
                  />
                  {isExpanded ? <ExpandLess /> : <ExpandMore />}
                </>
              )}
            </ListItemButton>
          </ListItem>
          {!sidebarCollapsed && (
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {item.children?.map(child => renderNavItem(child, level + 1))}
              </List>
            </Collapse>
          )}
        </React.Fragment>
      );
    }

    // Special handling for Dashboard to show parent active state when on sub-pages
    const isDashboard = item.id === 'dashboard';
    const dashboardParentActive = isDashboard && location.pathname !== '/dashboard' && location.pathname.startsWith('/dashboard');

    return (
      <React.Fragment key={item.id}>
        {divider}
        <ListItem disablePadding>
          <Tooltip
            title={sidebarCollapsed ? item.label : ''}
            placement="right"
            arrow
          >
            <ListItemButton
              selected={active}
              className={dashboardParentActive ? 'parent-active' : ''}
              onClick={() => item.path && handleNavigation(item.path)}
              sx={{
                pl: sidebarCollapsed ? 0 : level * 2 + 2,
                minHeight: 44,
                justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                px: sidebarCollapsed ? 1 : undefined,
              }}
            >
              <ListItemIcon sx={{ minWidth: sidebarCollapsed ? 0 : 40, justifyContent: 'center' }}>
                {item.badge ? (
                  <Badge badgeContent={item.badge} color="error">
                    {item.icon}
                  </Badge>
                ) : (
                  item.icon
                )}
              </ListItemIcon>
              {!sidebarCollapsed && (
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: (active || dashboardParentActive) ? 600 : 500
                  }}
                />
              )}
            </ListItemButton>
          </Tooltip>
        </ListItem>
      </React.Fragment>
    );
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo Section */}
      <Box sx={{
        p: sidebarCollapsed ? 1 : 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
        borderBottom: `1px solid ${muiTheme.palette.divider}`,
        minHeight: 64
      }}>
        <VideoLibrary
          sx={{
            color: muiTheme.palette.primary.main,
            fontSize: 32
          }}
        />
        {!sidebarCollapsed && (
          <Typography
            variant="h6"
            sx={{
              ml: 1,
              fontWeight: 700,
              color: muiTheme.palette.primary.main,
              letterSpacing: '-0.025em'
            }}
          >
            Griot
          </Typography>
        )}
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, py: 1, px: sidebarCollapsed ? 0.5 : 0 }}>
        <List>
          {filteredNavigationItems.map(item => renderNavItem(item))}
        </List>
      </Box>

      {/* Collapse Button */}
      {!isMobile && (
        <Box sx={{ p: 1, borderTop: `1px solid ${muiTheme.palette.divider}` }}>
          <Tooltip title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'} placement="right">
            <IconButton
              onClick={handleSidebarToggle}
              sx={{
                width: '100%',
                borderRadius: 2,
                '&:hover': {
                  backgroundColor: '#f1f5f9'
                }
              }}
            >
              {sidebarCollapsed ? <MenuIcon /> : <ChevronLeft />}
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Box>
  );

  const drawerWidth = sidebarCollapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH;

  return (
    <ThemeProvider theme={muiTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        {/* App Bar */}
        <AppBar
          position="fixed"
          sx={{
            width: { lg: `calc(100% - ${drawerWidth}px)` },
            ml: { lg: `${drawerWidth}px` },
            zIndex: muiTheme.zIndex.drawer + 1,
          }}
        >
          <Toolbar sx={{ justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{
                  mr: 2,
                  display: { lg: 'none' },
                  color: muiTheme.palette.mode === 'dark' ? '#e2e8f0' : '#1a202c',
                  '&:hover': {
                    backgroundColor: muiTheme.palette.mode === 'dark' ? 'rgba(148, 163, 184, 0.12)' : '#f1f5f9'
                  }
                }}
              >
                <MenuIcon />
              </IconButton>

              <Typography variant="h6" sx={{
                fontWeight: 600,
                color: muiTheme.palette.mode === 'dark' ? '#e2e8f0' : '#1a202c'
              }}>
                {location.pathname === '/' ? 'Dashboard' :
                  navigationItems.flatMap(item => [item, ...(item.children || [])])
                    .find(item => item.path === location.pathname)?.label || 'Griot'}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<MenuBook />}
                onClick={() => window.open('/docs', '_blank')}
                sx={{
                  display: { xs: 'none', md: 'flex' },
                  borderColor: muiTheme.palette.divider,
                  color: muiTheme.palette.mode === 'dark' ? '#cbd5f5' : '#64748b',
                  '&:hover': {
                    borderColor: muiTheme.palette.mode === 'dark' ? '#475569' : '#cbd5e1',
                    backgroundColor: muiTheme.palette.mode === 'dark' ? 'rgba(148, 163, 184, 0.12)' : '#f8fafc'
                  }
                }}
              >
                Docs
              </Button>

              <Tooltip title={`Switch to ${colorMode === 'light' ? 'dark' : 'light'} mode`}>
                <IconButton
                  onClick={toggleColorMode}
                  size="small"
                  color="inherit"
                  sx={{
                    '&:hover': {
                      backgroundColor: muiTheme.palette.mode === 'dark' ? 'rgba(148, 163, 184, 0.12)' : '#f1f5f9'
                    }
                  }}
                >
                  {colorMode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
                </IconButton>
              </Tooltip>

              <Tooltip title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}>
                <IconButton
                  onClick={handleToggleFullscreen}
                  size="small"
                  color="inherit"
                  sx={{
                    '&:hover': {
                      backgroundColor: muiTheme.palette.mode === 'dark' ? 'rgba(148, 163, 184, 0.12)' : '#f1f5f9'
                    }
                  }}
                >
                  {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                </IconButton>
              </Tooltip>

              <IconButton
                onClick={handleProfileMenuOpen}
                size="small"
                sx={{
                  '&:hover': {
                    backgroundColor: muiTheme.palette.mode === 'dark' ? 'rgba(148, 163, 184, 0.12)' : '#f1f5f9'
                  }
                }}
              >
                <Avatar sx={{
                  width: 36,
                  height: 36,
                  backgroundColor: muiTheme.palette.primary.main,
                  fontSize: '0.875rem',
                  fontWeight: 600
                }}>
                  <Person />
                </Avatar>
              </IconButton>

              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleProfileMenuClose}
                onClick={handleProfileMenuClose}
                slotProps={{
                  paper: {
                    elevation: 8,
                    sx: {
                      overflow: 'visible',
                      filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.15))',
                      mt: 1.5,
                      minWidth: 240,
                      borderRadius: 2,
                      border: `1px solid ${muiTheme.palette.divider}`,
                      '& .MuiAvatar-root': {
                        width: 32,
                        height: 32,
                        ml: -0.5,
                        mr: 1,
                      },
                    },
                  }
                }}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
              >
                <MenuItem disabled sx={{ opacity: 1 }}>
                  <Avatar sx={{ backgroundColor: muiTheme.palette.primary.main }}>
                    <Person />
                  </Avatar>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {userRole === 'admin' ? 'Administrator' : 'User'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {maskedApiKey}
                    </Typography>
                  </Box>
                </MenuItem>

                <Divider />

                <MenuItem onClick={() => { navigate('/dashboard/profile'); handleProfileMenuClose(); }}>
                  <Person sx={{ mr: 2, fontSize: 20 }} />
                  My Profile
                </MenuItem>

                <MenuItem onClick={() => { navigate('/dashboard/settings'); handleProfileMenuClose(); }}>
                  <Settings sx={{ mr: 2, fontSize: 20 }} />
                  Settings
                </MenuItem>

                <MenuItem onClick={() => window.open('/docs', '_blank')}>
                  <MenuBook sx={{ mr: 2, fontSize: 20 }} />
                  Documentation
                </MenuItem>

                <MenuItem onClick={() => { navigate('/dashboard/api-keys'); handleProfileMenuClose(); }}>
                  <ApiKeyIcon sx={{ mr: 2, fontSize: 20 }} />
                  API Keys
                </MenuItem>

                <Divider />

                <MenuItem onClick={handleLogout}>
                  <Logout sx={{ mr: 2, fontSize: 20 }} />
                  Logout
                </MenuItem>
              </Menu>
            </Box>
          </Toolbar>
        </AppBar>

        {/* Sidebar */}
        <Box
          component="nav"
          sx={{
            width: { lg: drawerWidth },
            flexShrink: { lg: 0 }
          }}
        >
          {/* Mobile drawer */}
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{
              keepMounted: true,
            }}
            sx={{
              display: { xs: 'block', lg: 'none' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: DRAWER_WIDTH
              },
            }}
          >
            {drawer}
          </Drawer>

          {/* Desktop drawer */}
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', lg: 'block' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: drawerWidth,
                transition: muiTheme.transitions.create('width', {
                  easing: muiTheme.transitions.easing.sharp,
                  duration: muiTheme.transitions.duration.enteringScreen,
                }),
              },
            }}
            open
          >
            {drawer}
          </Drawer>
        </Box>

        {/* Main content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            width: { lg: `calc(100% - ${drawerWidth}px)` },
            minHeight: '100vh',
            backgroundColor: muiTheme.palette.background.default,
          }}
        >
          <Toolbar />
          <Box sx={{
            p: { xs: 1.5, sm: 2, md: 3 },
            height: 'calc(100vh - 64px)',
            overflow: 'auto'
          }}>
            {children}
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default Layout;
