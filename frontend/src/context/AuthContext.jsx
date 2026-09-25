import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import {
  login as apiLogin,
  logout as apiLogout,
  getMe,
  getStoredToken,
  setStoredToken,
  clearStoredToken,
} from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [username, setUsername] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setChecking(false);
      return;
    }
    getMe()
      .then((res) => setUsername(res.data.username))
      .catch(() => clearStoredToken())
      .finally(() => setChecking(false));
  }, []);

  const login = useCallback(async (user, password) => {
    const response = await apiLogin(user, password);
    setStoredToken(response.data.token);
    setUsername(response.data.username);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {
      // le token est peut-être déjà invalide côté serveur, on nettoie quand même localement
    }
    clearStoredToken();
    setUsername(null);
  }, []);

  const value = {
    username,
    isAuthenticated: Boolean(username),
    checking,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth doit être utilisé à l’intérieur de <AuthProvider>');
  return ctx;
}
