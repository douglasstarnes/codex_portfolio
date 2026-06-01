import Link from "next/link";

import { AuthShell } from "@/components/auth/auth-shell";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <AuthShell
      title="Sign in"
      description="Use your portfolio account to continue."
      footer={
        <>
          Need an account?{" "}
          <Link className="font-medium text-foreground underline-offset-4 hover:underline" href="/register">
            Register
          </Link>
        </>
      }
    >
      <LoginForm />
    </AuthShell>
  );
}
