/**
 * Tests for type-safe API client functions.
 * Uses MSW to intercept requests at the network boundary.
 */
import { describe, it, expect } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { mockAccountsList, mockCategoriesList, mockCategoryTree } from '../mocks/fixtures';
import { fetchAccounts, fetchAccount, fetchCategories, fetchCategoryTree } from './api-client';

describe('Account API client', () => {
  it('fetchAccounts returns typed account list', async () => {
    const result = await fetchAccounts();

    expect(result).toEqual(mockAccountsList);
    expect(result.accounts).toHaveLength(4);
    expect(result.total).toBe(4);
    expect(result.accounts[0].id).toBe('acc_01234567890');
  });

  it('fetchAccount returns single account by ID', async () => {
    const result = await fetchAccount('acc_test123');

    expect(result.id).toBe('acc_test123');
    expect(result.name).toBe('Test Checking Account');
    expect(result.account_type).toBe('checking');
    expect(result.current_balance).toEqual({
      amount: '1500.00',
      currency: 'USD',
    });
  });

  it('fetchAccount handles 404 error', async () => {
    // Override handler to return 404
    server.use(
      http.get('http://localhost:8000/api/v1/accounts/:accountId', () => {
        return HttpResponse.json(
          {
            detail: {
              code: 'NOT_FOUND',
              message: 'Account not found',
            },
          },
          { status: 404 },
        );
      }),
    );

    await expect(fetchAccount('nonexistent')).rejects.toThrow();
  });

  it('fetchAccounts handles 500 error', async () => {
    // Override handler to return 500
    server.use(
      http.get('http://localhost:8000/api/v1/accounts', () => {
        return HttpResponse.json(
          {
            detail: {
              code: 'INTERNAL_ERROR',
              message: 'Database connection failed',
            },
          },
          { status: 500 },
        );
      }),
    );

    await expect(fetchAccounts()).rejects.toThrow();
  });
});

describe('Category API client', () => {
  it('fetchCategories returns typed category list', async () => {
    const result = await fetchCategories();

    expect(result).toEqual(mockCategoriesList);
    expect(result.categories).toHaveLength(2);
    expect(result.total).toBe(2);
    expect(result.categories[0].name).toBe('Groceries');
  });

  it('fetchCategoryTree returns tree structure', async () => {
    const result = await fetchCategoryTree();

    expect(result).toEqual(mockCategoryTree);
    expect(result.root).toHaveLength(1);
    expect(result.children).toEqual({});
  });

  it('fetchCategories handles network error', async () => {
    // Override handler to simulate network failure
    server.use(
      http.get('http://localhost:8000/api/v1/categories', () => {
        return HttpResponse.error();
      }),
    );

    await expect(fetchCategories()).rejects.toThrow();
  });
});
