"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Coins, ListChecks, Wallet } from "lucide-react";

import { AddTransactionDialog } from "@/components/dashboard/add-transaction-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatDateTime, formatQuantity } from "@/lib/format";
import type { Investment, PortfolioValue } from "@/lib/types";

type DashboardState = {
  portfolio: PortfolioValue | null;
  transactions: Investment[];
};

type ApiError = {
  detail?: string;
};

export function PortfolioDashboard() {
  const [state, setState] = useState<DashboardState>({
    portfolio: null,
    transactions: [],
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    setError(null);
    const [portfolioResponse, transactionsResponse] = await Promise.all([
      fetch("/api/portfolio/current-value", { cache: "no-store" }),
      fetch("/api/transactions", { cache: "no-store" }),
    ]);

    if (!portfolioResponse.ok) {
      const body = (await portfolioResponse.json()) as ApiError;
      throw new Error(body.detail ?? "Could not load the portfolio.");
    }

    if (!transactionsResponse.ok) {
      const body = (await transactionsResponse.json()) as ApiError;
      throw new Error(body.detail ?? "Could not load transactions.");
    }

    const [portfolio, transactions] = await Promise.all([
      portfolioResponse.json() as Promise<PortfolioValue>,
      transactionsResponse.json() as Promise<Investment[]>,
    ]);

    setState({ portfolio, transactions });
  }, []);

  useEffect(() => {
    refresh()
      .catch((caughtError: unknown) => {
        setError(caughtError instanceof Error ? caughtError.message : "Could not load dashboard data.");
      })
      .finally(() => setIsLoading(false));
  }, [refresh]);

  const latestTransactions = useMemo(
    () =>
      [...state.transactions].sort(
        (left, right) =>
          new Date(right.purchased_at).getTime() - new Date(left.purchased_at).getTime(),
      ),
    [state.transactions],
  );
  const holdingsCount = state.portfolio?.coins.length ?? 0;
  const buys = state.transactions.filter((transaction) => transaction.transaction_type === "buy").length;
  const sells = state.transactions.length - buys;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Portfolio</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Current value and transaction history for your account.
          </p>
        </div>
        <AddTransactionDialog onCreated={refresh} />
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          icon={<Wallet className="h-4 w-4" />}
          label="Current value"
          value={state.portfolio ? formatCurrency(state.portfolio.total_value_usd) : "$0.00"}
          isLoading={isLoading}
        />
        <MetricCard
          icon={<Coins className="h-4 w-4" />}
          label="Holdings"
          value={String(holdingsCount)}
          isLoading={isLoading}
        />
        <MetricCard
          icon={<ListChecks className="h-4 w-4" />}
          label="Transactions"
          value={String(state.transactions.length)}
          isLoading={isLoading}
        />
        <MetricCard
          icon={<Activity className="h-4 w-4" />}
          label="Buys / sells"
          value={`${buys} / ${sells}`}
          isLoading={isLoading}
        />
      </div>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.8fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Holdings</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? <TableSkeleton columns={5} /> : <HoldingsTable portfolio={state.portfolio} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent transactions</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? <TableSkeleton columns={4} /> : <TransactionsTable transactions={latestTransactions} />}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  isLoading,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  isLoading: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between text-muted-foreground">
          <span className="text-sm">{label}</span>
          {icon}
        </div>
        {isLoading ? (
          <Skeleton className="mt-4 h-8 w-28" />
        ) : (
          <p className="mt-3 text-2xl font-semibold tabular-nums">{value}</p>
        )}
      </CardContent>
    </Card>
  );
}

function HoldingsTable({ portfolio }: { portfolio: PortfolioValue | null }) {
  const coins = portfolio?.coins ?? [];

  if (!coins.length) {
    return <EmptyState message="No active holdings yet." />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Asset</TableHead>
          <TableHead className="text-right">Quantity</TableHead>
          <TableHead className="text-right">Price</TableHead>
          <TableHead className="text-right">Value</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {coins.map((coin) => (
          <TableRow key={coin.coingecko_id}>
            <TableCell>
              <div className="font-medium">{coin.symbol}</div>
              <div className="text-xs text-muted-foreground">{coin.coingecko_id}</div>
            </TableCell>
            <TableCell className="text-right tabular-nums">{formatQuantity(coin.quantity)}</TableCell>
            <TableCell className="text-right tabular-nums">{formatCurrency(coin.current_price_usd)}</TableCell>
            <TableCell className="text-right font-medium tabular-nums">{formatCurrency(coin.total_value_usd)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function TransactionsTable({ transactions }: { transactions: Investment[] }) {
  if (!transactions.length) {
    return <EmptyState message="No transactions recorded." />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Asset</TableHead>
          <TableHead>Type</TableHead>
          <TableHead className="text-right">Quantity</TableHead>
          <TableHead className="text-right">Price</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {transactions.map((transaction) => (
          <TableRow key={transaction.id}>
            <TableCell>
              <Link className="font-medium underline-offset-4 hover:underline" href={`/transactions/${transaction.id}`}>
                {transaction.symbol}
              </Link>
              <div className="text-xs text-muted-foreground">{formatDateTime(transaction.purchased_at)}</div>
            </TableCell>
            <TableCell>
              <Badge variant={transaction.transaction_type}>{transaction.transaction_type}</Badge>
            </TableCell>
            <TableCell className="text-right tabular-nums">{formatQuantity(transaction.quantity)}</TableCell>
            <TableCell className="text-right tabular-nums">{formatCurrency(transaction.purchase_price_usd)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function TableSkeleton({ columns }: { columns: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, rowIndex) => (
        <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }} key={rowIndex}>
          {Array.from({ length: columns }).map((__, columnIndex) => (
            <Skeleton className="h-8" key={columnIndex} />
          ))}
        </div>
      ))}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-32 items-center justify-center rounded-md border border-dashed text-sm text-muted-foreground">
      {message}
    </div>
  );
}
