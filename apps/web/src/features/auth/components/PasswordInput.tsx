import { useState, forwardRef } from 'react';
import { EyeOpenIcon, EyeClosedIcon } from '@radix-ui/react-icons';
import { Input, Button } from '@workspace/ui';

// Use forwardRef so react-hook-form's register can attach a ref
export const PasswordInput = forwardRef<HTMLInputElement, React.ComponentProps<typeof Input>>(
  function PasswordInput(props, ref) {
    const [showPassword, setShowPassword] = useState(false);

    return (
      <div className="relative">
        <Input type={showPassword ? 'text' : 'password'} ref={ref} {...props} className="pr-10" />
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          onClick={() => setShowPassword(!showPassword)}
          tabIndex={-1}
          aria-label={showPassword ? 'Hide password' : 'Show password'}
        >
          {showPassword ? <EyeClosedIcon className="size-4" /> : <EyeOpenIcon className="size-4" />}
        </Button>
      </div>
    );
  },
);
