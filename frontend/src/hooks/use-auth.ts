import type { PlatformUser } from "../types";
import type { AuthCredentials } from "../lib/api";

const localAdminUser: PlatformUser = {
  id: 1,
  username: "本地管理员"
};

export function useAuth() {
  return {
    status: "authenticated" as const,
    user: localAdminUser,
    error: null,
    isAuthenticated: true,
    isChecking: false,
    login: async (_credentials?: AuthCredentials) => {},
    register: async (_credentials?: AuthCredentials) => {},
    logout: async () => {
      window.location.reload();
    }
  };
}
