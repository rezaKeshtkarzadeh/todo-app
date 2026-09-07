import { useAppDispatch } from "@/store/hooks";
import { useRouter } from "next/navigation";

export function useAuthCleanup() {
  const dispatch = useAppDispatch();
  const router = useRouter();

  return () => {
    // Reset Redux slices
    dispatch({ type: "auth/setUnauthenticated" });
    dispatch({ type: "tasks/setTasks", payload: [] });
    dispatch({ type: "profile/setAvatarUrl", payload: null });
    dispatch({ type: "security/setDevices", payload: [] });

    // Clear theme and locale from localStorage, preserve device_id
    if (typeof window !== "undefined") {
      localStorage.removeItem("theme");
      localStorage.removeItem("locale");
    }

    // Redirect to login
    router.push("/login");
  };
}