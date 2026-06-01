"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type RegisterResponse = {
  detail?: string;
};

export function RegisterForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "").trim();
    const payload = {
      username: String(formData.get("username") ?? ""),
      email: email.length ? email : null,
      password: String(formData.get("password") ?? ""),
    };

    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = (await response.json()) as RegisterResponse;

    setIsSubmitting(false);

    if (!response.ok) {
      setError(data.detail ?? "Could not create the account.");
      return;
    }

    router.push("/login");
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}
      <div className="space-y-2">
        <Label htmlFor="username">Username</Label>
        <Input id="username" name="username" maxLength={50} autoComplete="username" required />
      </div>
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" name="email" type="email" maxLength={255} autoComplete="email" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          name="password"
          type="password"
          minLength={8}
          maxLength={128}
          autoComplete="new-password"
          required
        />
      </div>
      <Button className="w-full" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Creating account..." : "Create account"}
      </Button>
    </form>
  );
}
