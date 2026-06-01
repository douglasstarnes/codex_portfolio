"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { InvestmentCreate, TransactionType } from "@/lib/types";

type AddTransactionDialogProps = {
  onCreated: () => Promise<void>;
};

type ApiResponse = {
  detail?: string;
};

function localDateTimeValue() {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

export function AddTransactionDialog({ onCreated }: AddTransactionDialogProps) {
  const [open, setOpen] = useState(false);
  const [transactionType, setTransactionType] = useState<TransactionType>("buy");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = event.currentTarget;
    const formData = new FormData(form);
    const name = String(formData.get("name") ?? "").trim();
    const purchasedAt = String(formData.get("purchased_at") ?? "");
    const payload: InvestmentCreate = {
      symbol: String(formData.get("symbol") ?? "").trim().toUpperCase(),
      coingecko_id: String(formData.get("coingecko_id") ?? "").trim(),
      name: name.length ? name : null,
      quantity: String(formData.get("quantity") ?? ""),
      transaction_type: transactionType,
      purchased_at: purchasedAt ? new Date(purchasedAt).toISOString() : undefined,
    };

    const response = await fetch("/api/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = (await response.json()) as ApiResponse;

    setIsSubmitting(false);

    if (!response.ok) {
      setError(data.detail ?? "Could not save the transaction.");
      return;
    }

    form.reset();
    setTransactionType("buy");
    setOpen(false);
    await onCreated();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add transaction
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add transaction</DialogTitle>
          <DialogDescription>Record a buy or sell for the current portfolio.</DialogDescription>
        </DialogHeader>
        <form className="grid gap-4" onSubmit={onSubmit}>
          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="symbol">Symbol</Label>
              <Input id="symbol" name="symbol" maxLength={16} placeholder="BTC" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="coingecko_id">CoinGecko id</Label>
              <Input id="coingecko_id" name="coingecko_id" maxLength={100} placeholder="bitcoin" required />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" name="name" maxLength={100} placeholder="Bitcoin" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="quantity">Quantity</Label>
              <Input id="quantity" name="quantity" type="number" min="0" step="any" placeholder="0.01" required />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={transactionType} onValueChange={(value: TransactionType) => setTransactionType(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="buy">Buy</SelectItem>
                  <SelectItem value="sell">Sell</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="purchased_at">Purchased at</Label>
              <Input id="purchased_at" name="purchased_at" type="datetime-local" defaultValue={localDateTimeValue()} />
            </div>
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : "Save transaction"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
