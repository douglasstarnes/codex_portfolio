export type TransactionType = "buy" | "sell";

export type UserRead = {
  id: number;
  username: string;
  email: string | null;
  is_active: boolean;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
};

export type Investment = {
  id: number;
  symbol: string;
  coingecko_id: string;
  name: string | null;
  quantity: string;
  transaction_type: TransactionType;
  purchase_price_usd: string;
  purchased_at: string;
};

export type InvestmentCreate = {
  symbol: string;
  coingecko_id: string;
  name?: string | null;
  quantity: string;
  transaction_type: TransactionType;
  purchased_at?: string;
};

export type CoinValue = {
  symbol: string;
  coingecko_id: string;
  quantity: string;
  current_price_usd: string;
  total_value_usd: string;
};

export type PortfolioValue = {
  coins: CoinValue[];
  total_value_usd: string;
};

export type ApiErrorBody = {
  detail?: string;
  message?: string;
};
