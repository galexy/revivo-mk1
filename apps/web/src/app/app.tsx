import { useEffect, useState } from 'react';
import { Button, Card, CardHeader, CardTitle, CardContent, Input, Label } from '@workspace/ui';

/**
 * Legacy App component - content will be moved to DashboardPage in Plan 05
 * This component is temporarily preserved for reference but is no longer used in routing
 */
export function App() {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window === 'undefined') return false;
    const stored = localStorage.getItem('theme');
    return (
      stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches)
    );
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* Left Sidebar */}
      <aside className="w-[var(--sidebar-width)] border-r border-border bg-card p-4 flex flex-col gap-4">
        <h2 className="text-lg font-semibold text-primary">Accounts</h2>
        <nav className="space-y-1">
          <div className="px-3 py-2 rounded-md bg-accent text-accent-foreground text-sm font-medium">
            Checking
          </div>
          <div className="px-3 py-2 rounded-md text-muted-foreground text-sm hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer">
            Savings
          </div>
          <div className="px-3 py-2 rounded-md text-muted-foreground text-sm hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer">
            Credit Card
          </div>
        </nav>
        <div className="mt-auto">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsDark(!isDark)}
            className="w-full justify-start"
          >
            {isDark ? 'Light' : 'Dark'} Mode
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 space-y-6">
        <h1 className="text-2xl font-bold">Personal Finance</h1>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Checking</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold font-mono">$1,234.56</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Savings</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold font-mono">$15,678.90</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Credit Card</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold font-mono amount-negative">-$542.30</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Quick Add Transaction</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="payee">Payee</Label>
              <Input id="payee" placeholder="Enter payee name" />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="amount">Amount</Label>
              <Input id="amount" type="number" placeholder="0.00" className="font-mono" />
            </div>
            <Button>Add Transaction</Button>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
