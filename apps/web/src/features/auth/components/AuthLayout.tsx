import { type ReactNode } from 'react';

function LogoIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className}>
      <path
        d="M3 9a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V9Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path d="M3 11h18" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="17" cy="16" r="1.5" fill="currentColor" />
      <path d="M7 6V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

function SocialProof() {
  return (
    <div className="flex items-center gap-4">
      <div className="flex -space-x-2">
        {['bg-blue-500', 'bg-violet-500', 'bg-emerald-500', 'bg-amber-500'].map((bg, i) => (
          <div
            key={i}
            className={`flex size-8 items-center justify-center rounded-full border-2 border-slate-900 text-[10px] font-bold text-white ${bg}`}
          >
            {['AW', 'RK', 'SL', 'MJ'][i]}
          </div>
        ))}
      </div>
      <div>
        <div className="flex items-center gap-1">
          {[...Array(5)].map((_, i) => (
            <svg
              key={i}
              viewBox="0 0 16 16"
              fill="currentColor"
              className="size-3.5 text-amber-400"
            >
              <path d="M8 1.318l1.91 3.87 4.27.621-3.09 3.01.73 4.253L8 11.052l-3.82 2.01.73-4.254-3.09-3.01 4.27-.62L8 1.317Z" />
            </svg>
          ))}
        </div>
        <p className="mt-0.5 text-xs text-slate-500">Trusted by 2,400+ households</p>
      </div>
    </div>
  );
}

interface AuthLayoutProps {
  isLoading: boolean;
  leftContent: ReactNode;
  title: string;
  description: string;
  children: ReactNode;
  footer: string;
}

export function AuthLayout({
  isLoading,
  leftContent,
  title,
  description,
  children,
  footer,
}: AuthLayoutProps) {
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex items-center gap-3 text-muted-foreground">
          <svg className="size-5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="3"
              className="opacity-20"
            />
            <path
              d="M12 2a10 10 0 0 1 10 10"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      {/* Left branded panel */}
      <div className="relative hidden w-[52%] overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 lg:flex lg:flex-col">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0">
          <div
            className="absolute inset-0 opacity-[0.04]"
            style={{
              backgroundImage: 'radial-gradient(rgba(255,255,255,0.15) 1px, transparent 1px)',
              backgroundSize: '24px 24px',
            }}
          />
          <div className="absolute -right-32 -top-32 size-[500px] rounded-full bg-indigo-500/15 blur-[120px]" />
          <div className="absolute -bottom-48 -left-24 size-96 rounded-full bg-blue-600/10 blur-[100px]" />
          <div className="absolute right-1/3 top-1/2 size-72 rounded-full bg-emerald-500/8 blur-[80px]" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-1 flex-col justify-between p-10 xl:p-12">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-400 to-cyan-500 shadow-lg shadow-emerald-500/20">
              <LogoIcon className="size-5 text-white" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-white">Revivo</span>
          </div>

          {/* Center content */}
          <div className="flex flex-col items-center">{leftContent}</div>

          {/* Social proof */}
          <SocialProof />
        </div>
      </div>

      {/* Right form panel */}
      <div className="relative flex flex-1 flex-col bg-background">
        <div className="pointer-events-none absolute right-0 top-0 size-96 rounded-full bg-primary/[0.03] blur-3xl" />

        {/* Mobile header */}
        <div className="flex items-center gap-2.5 p-6 lg:hidden">
          <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-400 to-cyan-500">
            <LogoIcon className="size-4 text-white" />
          </div>
          <span className="font-semibold">Revivo</span>
        </div>

        {/* Form area */}
        <div className="flex flex-1 items-center justify-center px-6 py-12 sm:px-12">
          <div className="relative z-10 w-full max-w-[380px] space-y-8">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>

            {children}

            <p className="text-center text-xs text-muted-foreground/60">{footer}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
