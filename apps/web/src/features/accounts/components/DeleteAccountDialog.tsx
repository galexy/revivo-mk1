/**
 * Delete Account Confirmation Dialog
 * Requires user to type account name to confirm deletion.
 * Prevents accidental data loss with type-to-confirm pattern.
 */
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@workspace/ui';
import { Input, Label, Button } from '@workspace/ui';

interface DeleteAccountDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountName: string;
  accountId: string;
  onConfirmDelete: (id: string) => void;
}

export function DeleteAccountDialog({
  open,
  onOpenChange,
  accountName,
  accountId,
  onConfirmDelete,
}: DeleteAccountDialogProps) {
  const [confirmText, setConfirmText] = useState('');

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setConfirmText('');
    }
  }, [open]);

  const handleClose = () => {
    setConfirmText('');
    onOpenChange(false);
  };

  const handleDelete = () => {
    if (confirmText === accountName) {
      onConfirmDelete(accountId);
      handleClose();
    }
  };

  const isConfirmed = confirmText === accountName;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Account</DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete the
            account <strong>{accountName}</strong> and all associated
            transactions.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="confirmText">
            Type <strong>{accountName}</strong> to confirm
          </Label>
          <Input
            id="confirmText"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder={`Type "${accountName}" to confirm`}
            autoComplete="off"
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={!isConfirmed}>
            Delete Account
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
