"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatDateTime, formatQuantity } from "@/lib/format";
import type { Investment } from "@/lib/types";

type TransactionDetailProps = {
  id: string;
};

type ApiError = {
  detail?: string;
};

export function TransactionDetail({ id }: TransactionDetailProps) {
  const [transaction, setTransaction] = useState<Investment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/transactions/${id}`, { cache: "no-store" })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          const errorBody = data as ApiError;
          throw new Error(errorBody.detail ?? "Could not load the transaction.");
        }

        setTransaction(data as Investment);
      })
      .catch((caughtError: unknown) => {
        setError(caughtError instanceof Error ? caughtError.message : "Could not load the transaction.");
      })
      .finally(() => setIsLoading(false));
  }, [id]);

  return (
    <div className="space-y-6">
      <Button asChild variant="outline" size="sm">
        <Link href="/dashboard">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Dashboard
        </Link>
      </Button>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Transaction detail</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: 8 }).map((_, index) => (
                <Skeleton className="h-16" key={index} />
              ))}
            </div>
          ) : transaction ? (
            <dl className="grid gap-4 sm:grid-cols-2">
              <DetailItem label="Symbol" value={transaction.symbol} />
              <DetailItem label="Name" value={transaction.name ?? "Not set"} />
              <DetailItem label="CoinGecko id" value={transaction.coingecko_id} />
              <div className="rounded-md border p-4">
                <dt className="text-xs uppercase text-muted-foreground">Type</dt>
                <dd className="mt-2">
                  <Badge variant={transaction.transaction_type}>{transaction.transaction_type}</Badge>
                </dd>
              </div>
              <DetailItem label="Quantity" value={formatQuantity(transaction.quantity)} />
              <DetailItem label="Purchase price" value={formatCurrency(transaction.purchase_price_usd)} />
              <DetailItem label="Purchased at" value={formatDateTime(transaction.purchased_at)} />
              <DetailItem label="Transaction id" value={String(transaction.id)} />
            </dl>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-4">
      <dt className="text-xs uppercase text-muted-foreground">{label}</dt>
      <dd className="mt-2 font-medium tabular-nums">{value}</dd>
    </div>
  );
}
