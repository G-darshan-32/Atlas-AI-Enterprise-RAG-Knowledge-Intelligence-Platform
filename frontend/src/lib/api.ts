import axios, { AxiosInstance, AxiosError } from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export const api: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  withCredentials: false,
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => (error ? prom.reject(error) : prom.resolve(token!)));
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest!.headers!.Authorization = `Bearer ${token}`;
          return api(originalRequest!);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) {
        isRefreshing = false;
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const res = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, { refresh_token: refreshToken });
        const { access_token, refresh_token: newRefresh } = res.data;
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("refresh_token", newRefresh);
        api.defaults.headers.common.Authorization = `Bearer ${access_token}`;
        processQueue(null, access_token);
        return api(originalRequest!);
      } catch (err) {
        processQueue(err, null);
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ─── API helpers ─────────────────────────────────────────

export const authApi = {
  register: (data: { email: string; password: string; full_name: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post<{ access_token: string; refresh_token: string }>("/auth/login", data),
  logout: (refreshToken: string) => api.post("/auth/logout", { refresh_token: refreshToken }),
  me: () => api.get("/auth/me"),
  updateProfile: (data: { full_name?: string; avatar_url?: string }) => api.put("/auth/me", data),
  forgotPassword: (email: string) => api.post("/auth/forgot-password", { email }),
  resetPassword: (token: string, password: string) =>
    api.post("/auth/reset-password", { token, new_password: password }),
};

export const workspaceApi = {
  list: () => api.get("/workspaces"),
  create: (data: { name: string; description?: string }) => api.post("/workspaces", data),
  get: (id: string) => api.get(`/workspaces/${id}`),
  update: (id: string, data: object) => api.put(`/workspaces/${id}`, data),
  delete: (id: string) => api.delete(`/workspaces/${id}`),
  listMembers: (id: string) => api.get(`/workspaces/${id}/members`),
  inviteMember: (id: string, data: { email: string; role: string }) =>
    api.post(`/workspaces/${id}/members/invite`, data),
  updateMemberRole: (workspaceId: string, userId: string, role: string) =>
    api.put(`/workspaces/${workspaceId}/members/${userId}/role`, { role }),
  removeMember: (workspaceId: string, userId: string) =>
    api.delete(`/workspaces/${workspaceId}/members/${userId}`),
  getStorage: (id: string) => api.get(`/workspaces/${id}/storage`),
  getAnalytics: (id: string) => api.get(`/workspaces/${id}/analytics/overview`),
};

export const documentApi = {
  list: (workspaceId: string, params?: object) =>
    api.get(`/workspaces/${workspaceId}/documents`, { params }),
  upload: (workspaceId: string, file: File, folderId?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (folderId) form.append("folder_id", folderId);
    return api.post(`/workspaces/${workspaceId}/documents/upload`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  get: (workspaceId: string, docId: string) =>
    api.get(`/workspaces/${workspaceId}/documents/${docId}`),
  delete: (workspaceId: string, docId: string) =>
    api.delete(`/workspaces/${workspaceId}/documents/${docId}`),
  getPreviewUrl: (workspaceId: string, docId: string) =>
    api.get(`/workspaces/${workspaceId}/documents/${docId}/preview`),
  listFolders: (workspaceId: string) => api.get(`/workspaces/${workspaceId}/folders`),
  createFolder: (workspaceId: string, name: string) =>
    api.post(`/workspaces/${workspaceId}/folders`, { name }),
};

export const chatApi = {
  listSessions: (workspaceId: string) =>
    api.get(`/workspaces/${workspaceId}/chat/sessions`),
  createSession: (workspaceId: string, mode: string = "general") =>
    api.post(`/workspaces/${workspaceId}/chat/sessions`, { mode }, { params: { mode } }),
  getSession: (workspaceId: string, sessionId: string) =>
    api.get(`/workspaces/${workspaceId}/chat/sessions/${sessionId}`),
  deleteSession: (workspaceId: string, sessionId: string) =>
    api.delete(`/workspaces/${workspaceId}/chat/sessions/${sessionId}`),
  togglePin: (workspaceId: string, sessionId: string) =>
    api.put(`/workspaces/${workspaceId}/chat/sessions/${sessionId}/pin`),
};

export const searchApi = {
  search: (workspaceId: string, query: string, filters?: object, limit?: number) =>
    api.post(`/workspaces/${workspaceId}/search`, { query, filters, limit }),
};

export const analyticsApi = {
  overview: (workspaceId: string) =>
    api.get(`/workspaces/${workspaceId}/analytics/overview`),
  documents: (workspaceId: string) =>
    api.get(`/workspaces/${workspaceId}/analytics/documents`),
  chat: (workspaceId: string, days?: number) =>
    api.get(`/workspaces/${workspaceId}/analytics/chat`, { params: { days } }),
};

export const githubApi = {
  listRepos: (workspaceId: string) =>
    api.get(`/workspaces/${workspaceId}/github/repos`),
  connectRepo: (workspaceId: string, data: object) =>
    api.post(`/workspaces/${workspaceId}/github/repos/connect`, data),
  syncRepo: (workspaceId: string, repoId: string) =>
    api.post(`/workspaces/${workspaceId}/github/repos/${repoId}/sync`),
  disconnectRepo: (workspaceId: string, repoId: string) =>
    api.delete(`/workspaces/${workspaceId}/github/repos/${repoId}`),
};

export const notificationApi = {
  list: (unreadOnly?: boolean) =>
    api.get("/notifications", { params: { unread_only: unreadOnly } }),
  markRead: (id: string) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post("/notifications/read-all"),
};
