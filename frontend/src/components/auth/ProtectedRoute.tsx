"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { checkAuth } from "@/store/slices/authSlice";
import { Skeleton } from "@/components/ui/skeleton";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { isAuthenticated, status } = useAppSelector((state) => state.auth);

  // Only check auth on initial load (when status is idle and not authenticated)
  useEffect(() => {
    if (status === "idle" && !isAuthenticated) {
      dispatch(checkAuth());
    }
  }, [dispatch, isAuthenticated, status]);

  useEffect(() => {
    if (status === "idle" && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, status, router]);

  // Show loading skeleton while checking auth
  if (status === "loading") {
    return (
      <div className="container mx-auto py-8 px-4">
        <Skeleton className="h-8 w-48 mb-4" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      </div>
    );
  }

  // Don't render children if not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}