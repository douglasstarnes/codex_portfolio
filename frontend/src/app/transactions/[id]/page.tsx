import { AppShell } from "@/components/app-shell";
import { TransactionDetail } from "@/components/transactions/transaction-detail";

type TransactionPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function TransactionPage({ params }: TransactionPageProps) {
  const { id } = await params;

  return (
    <AppShell>
      <TransactionDetail id={id} />
    </AppShell>
  );
}
