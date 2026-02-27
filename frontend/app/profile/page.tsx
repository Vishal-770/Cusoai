"use client";

import { useSession, signOut } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Mail, ShieldCheck, User, KeyRound, LogOut } from "lucide-react";

export default function ProfilePage() {
  const { data: session, isPending } = useSession();
  const router = useRouter();

  const handleSignOut = async () => {
    await signOut({
      fetchOptions: { onSuccess: () => router.push("/login") },
    });
  };

  if (isPending) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (!session) return null;

  const initials = session.user.name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col bg-background">
      <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-10 space-y-8">
        {/* Profile Header */}
        <Card>
          <CardContent className="flex flex-col gap-6 pt-6 sm:flex-row sm:items-center">
            <Avatar className="h-20 w-20">
              <AvatarImage
                src={session.user.image ?? undefined}
                alt={session.user.name}
              />
              <AvatarFallback className="text-2xl">{initials}</AvatarFallback>
            </Avatar>
            <div className="flex-1 space-y-1">
              <h1 className="text-2xl font-semibold text-foreground">
                {session.user.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                {session.user.email}
              </p>
              <div className="flex flex-wrap gap-2 pt-1">
                <Badge variant="secondary">Google OAuth</Badge>
                {session.user.emailVerified && (
                  <Badge variant="outline" className="text-xs">
                    <ShieldCheck className="mr-1 h-3 w-3" />
                    Verified
                  </Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Account Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account Details</CardTitle>
            <CardDescription>
              Your profile information from Google.
            </CardDescription>
          </CardHeader>
          <Separator />
          <CardContent className="divide-y">
            <DetailRow
              icon={<User className="h-4 w-4" />}
              label="Full Name"
              value={session.user.name}
            />
            <DetailRow
              icon={<Mail className="h-4 w-4" />}
              label="Email Address"
              value={session.user.email}
            />
            <DetailRow
              icon={<ShieldCheck className="h-4 w-4" />}
              label="Auth Provider"
              value="Google"
            />
            <DetailRow
              icon={<KeyRound className="h-4 w-4" />}
              label="Account ID"
              value={session.user.id}
              mono
            />
          </CardContent>
        </Card>

        {/* Sign Out */}
        <div className="flex justify-end">
          <Button
            variant="outline"
            onClick={handleSignOut}
            className="gap-2 text-destructive hover:text-destructive"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </main>
    </div>
  );
}

function DetailRow({
  icon,
  label,
  value,
  mono = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-4 py-4">
      <span className="mt-0.5 text-muted-foreground">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <p
          className={`mt-0.5 truncate text-sm text-foreground ${mono ? "font-mono" : ""}`}
        >
          {value}
        </p>
      </div>
    </div>
  );
}
