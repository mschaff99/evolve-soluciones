/**
 * Auth Slice
 * ==========
 * Manejo del estado de autenticación con Redux Toolkit
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { authService } from '@/api/services/auth.service';
import type { AuthState, LoginRequest, Usuario } from '@/types/auth.types';

const initialState: AuthState = {
  usuario: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

// Thunks asíncronos
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await authService.login(credentials);
      return response;
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.error || 'Error al iniciar sesión'
      );
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.error || 'Error al cerrar sesión'
      );
    }
  }
);

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const usuario = await authService.getCurrentUser();
      return usuario;
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.error || 'Error al obtener usuario'
      );
    }
  }
);

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setUsuario: (state, action: PayloadAction<Usuario>) => {
      state.usuario = action.payload;
      state.isAuthenticated = true;
    },
  },
  extraReducers: (builder) => {
    // Login
    builder.addCase(login.pending, (state) => {
      state.isLoading = true;
      state.error = null;
    });
    builder.addCase(login.fulfilled, (state, action) => {
      state.isLoading = false;
      state.isAuthenticated = true;
      state.usuario = action.payload.usuario;
      state.error = null;
    });
    builder.addCase(login.rejected, (state, action) => {
      state.isLoading = false;
      state.isAuthenticated = false;
      state.usuario = null;
      state.error = action.payload as string;
    });

    // Logout
    builder.addCase(logout.fulfilled, (state) => {
      state.isAuthenticated = false;
      state.usuario = null;
      state.error = null;
    });

    // Get current user
    builder.addCase(getCurrentUser.pending, (state) => {
      state.isLoading = true;
    });
    builder.addCase(getCurrentUser.fulfilled, (state, action) => {
      state.isLoading = false;
      state.isAuthenticated = true;
      state.usuario = action.payload;
    });
    builder.addCase(getCurrentUser.rejected, (state) => {
      state.isLoading = false;
      state.isAuthenticated = false;
      state.usuario = null;
    });
  },
});

export const { clearError, setUsuario } = authSlice.actions;
export default authSlice.reducer;
