import Link from "next/link";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type AuthShellProps = {
  title: string;
  description: string;
  footer: React.ReactNode;
  children: React.ReactNode;
};

export function AuthShell({ title, description, footer, children }: AuthShellProps) {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <Link href="/" className="block text-center text-lg font-semibold">
          Codex Portfolio
        </Link>
        <Card>
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {children}
            <div className="text-center text-sm text-muted-foreground">{footer}</div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
