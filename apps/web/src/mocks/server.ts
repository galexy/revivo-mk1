/**
 * MSW server setup for Node.js test environment.
 * Imported and started in test-setup.ts.
 */
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
