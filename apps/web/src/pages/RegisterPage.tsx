import { useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useAuth } from '../features/auth/context/useAuth';
import { RegisterForm } from '../features/auth/components/RegisterForm';
import { AuthLayout } from '../features/auth/components/AuthLayout';

function FeatureItem({
  icon,
  title,
  desc,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-white/[0.07]">
        {icon}
      </div>
      <div>
        <p className="text-sm font-medium text-white">{title}</p>
        <p className="mt-0.5 text-sm text-slate-400">{desc}</p>
      </div>
    </div>
  );
}

function RegisterHeroContent() {
  return (
    <div className="w-full max-w-md space-y-10">
      <div className="space-y-3 text-center">
        <h1 className="text-3xl font-bold leading-tight tracking-tight text-white xl:text-4xl">
          Start your{' '}
          <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            financial journey.
          </span>
        </h1>
        <p className="text-base leading-relaxed text-slate-400">
          Join thousands of households taking control of their money with Revivo.
        </p>
      </div>

      {/* Feature highlights */}
      <div className="space-y-6">
        <FeatureItem
          icon={
            <svg viewBox="0 0 20 20" fill="currentColor" className="size-5 text-emerald-400">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.857-9.809a.75.75 0 0 0-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 1 0-1.06 1.061l2.5 2.5a.75.75 0 0 0 1.137-.089l4-5.5Z"
                clipRule="evenodd"
              />
            </svg>
          }
          title="Free to get started"
          desc="No credit card required. Start tracking in under 2 minutes."
        />
        <FeatureItem
          icon={
            <svg viewBox="0 0 20 20" fill="currentColor" className="size-5 text-blue-400">
              <path
                fillRule="evenodd"
                d="M10 1a4.5 4.5 0 0 0-4.5 4.5V9H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2h-.5V5.5A4.5 4.5 0 0 0 10 1Zm3 8V5.5a3 3 0 1 0-6 0V9h6Z"
                clipRule="evenodd"
              />
            </svg>
          }
          title="Private & secure"
          desc="Your data is encrypted and never sold to third parties."
        />
        <FeatureItem
          icon={
            <svg viewBox="0 0 20 20" fill="currentColor" className="size-5 text-violet-400">
              <path d="M1 4.25a3.733 3.733 0 0 1 2.25-.75h13.5c.844 0 1.623.279 2.25.75A2.25 2.25 0 0 0 16.75 2H3.25A2.25 2.25 0 0 0 1 4.25ZM1 7.25a3.733 3.733 0 0 1 2.25-.75h13.5c.844 0 1.623.279 2.25.75A2.25 2.25 0 0 0 16.75 5H3.25A2.25 2.25 0 0 0 1 7.25ZM7 8a1 1 0 0 1 1 1 2 2 0 1 0 4 0 1 1 0 0 1 1-1h3.75A2.25 2.25 0 0 1 19 10.25v5.5A2.25 2.25 0 0 1 16.75 18H3.25A2.25 2.25 0 0 1 1 15.75v-5.5A2.25 2.25 0 0 1 3.25 8H7Z" />
            </svg>
          }
          title="All accounts in one view"
          desc="Checking, savings, investments, and credit — unified."
        />
      </div>
    </div>
  );
}

export function RegisterPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate({ to: '/dashboard' });
    }
  }, [isAuthenticated, isLoading, navigate]);

  return (
    <AuthLayout
      isLoading={isLoading}
      leftContent={<RegisterHeroContent />}
      title="Create your account"
      description="Get started for free — no credit card required"
      footer="By creating an account, you agree to our Terms of Service and Privacy Policy."
    >
      <RegisterForm />
    </AuthLayout>
  );
}
