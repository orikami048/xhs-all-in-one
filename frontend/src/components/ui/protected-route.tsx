import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

type RouteGuardProps = {
  children: ReactNode;
};

// 免登录模式：所有受保护路由直接开放放行
export function ProtectedRoute({ children }: RouteGuardProps) {
  return <>{children}</>;
}

// 登录页直接重定向到小红书面板
export function PublicOnlyRoute({ children }: RouteGuardProps) {
  return <Navigate to="/platforms/xhs/dashboard" replace />;
}
