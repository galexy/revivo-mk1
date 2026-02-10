import { useState } from 'react';

export function App() {
  // Initialize dark mode state from localStorage or system preference
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem('theme');
    const shouldBeDark =
      stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches);
    if (shouldBeDark) {
      document.documentElement.classList.add('dark');
    }
    return shouldBeDark;
  });

  const toggleTheme = () => {
    const next = !isDark;
    setIsDark(next);
    document.documentElement.classList.toggle('dark', next);
    localStorage.setItem('theme', next ? 'dark' : 'light');
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-primary">Personal Finance</h1>
          <button
            onClick={toggleTheme}
            className="px-4 py-2 rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
          >
            {isDark ? 'Light' : 'Dark'} Mode
          </button>
        </div>
        <p className="text-muted-foreground">App is running with Tailwind CSS v4.</p>
        <div className="font-mono text-lg">
          <span>Balance: </span>
          <span className="text-success-foreground">$1,234.56</span>
          <span className="mx-4">|</span>
          <span className="amount-negative">-$50.00</span>
        </div>
      </div>
    </div>
  );
}
