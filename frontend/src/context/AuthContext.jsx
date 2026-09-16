import { createContext, useState, useEffect, useContext, useRef } from 'react';
import { jwtDecode } from 'jwt-decode';
import { authApi } from '../api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const isInitiating = useRef(false);

    const fetchProfile = async (token) => {
        try {
            const decoded = jwtDecode(token);
            const response = await authApi.getMe(decoded.sub);
            setUser(response.data);
        } catch (error) {
            console.error("Failed to fetch profile:", error);
            logout();
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isInitiating.current) return;
        isInitiating.current = true;

        const initAuth = async () => {
            const accessToken = localStorage.getItem('access_token');
            const refreshToken = localStorage.getItem('refresh_token');

            if (accessToken) {
                await fetchProfile(accessToken);
            } else if (refreshToken) {
                try {
                    const response = await authApi.refreshToken(refreshToken);
                    const { access_token, refresh_token: newRefreshToken } = response.data;
                    
                    localStorage.setItem('access_token', access_token);
                    if (newRefreshToken) localStorage.setItem('refresh_token', newRefreshToken);
                    
                    await fetchProfile(access_token);
                } catch (error) {
                    console.error("Init refresh failed:", error);
                    logout();
                    setLoading(false);
                }
            } else {
                setLoading(false);
            }
        };

        initAuth();
    }, []);

    const login = async (email, password) => {
        const response = await authApi.login(email, password);
        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        await fetchProfile(access_token);
    };

    const register = async (name, email, password) => {
        await authApi.register({ name, email, password });
        await login(email, password);
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
