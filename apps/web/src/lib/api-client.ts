/**
 * Type-safe API client built on existing Axios instance.
 * Uses generated OpenAPI types for request/response typing.
 */
import api from './api';
import type { components } from './api-types.generated';

// Type aliases for commonly used response types
export type AccountResponse = components['schemas']['AccountResponse'];
export type AccountListResponse = components['schemas']['AccountListResponse'];
export type TransactionResponse = components['schemas']['TransactionResponse'];
export type TransactionListResponse = components['schemas']['TransactionListResponse'];
export type CategoryResponse = components['schemas']['CategoryResponse'];
export type CategoryListResponse = components['schemas']['CategoryListResponse'];
export type CategoryTreeResponse = components['schemas']['CategoryTreeResponse'];

export type CreateCheckingAccountRequest = components['schemas']['CreateCheckingAccountRequest'];
export type CreateSavingsAccountRequest = components['schemas']['CreateSavingsAccountRequest'];
export type CreateCreditCardAccountRequest =
  components['schemas']['CreateCreditCardAccountRequest'];
export type CreateLoanAccountRequest = components['schemas']['CreateLoanAccountRequest'];
export type CreateBrokerageAccountRequest = components['schemas']['CreateBrokerageAccountRequest'];
export type CreateIraAccountRequest = components['schemas']['CreateIraAccountRequest'];
export type CreateRewardsAccountRequest = components['schemas']['CreateRewardsAccountRequest'];
export type UpdateAccountRequest = components['schemas']['UpdateAccountRequest'];

export type CreateTransactionRequest = components['schemas']['CreateTransactionRequest'];
export type UpdateTransactionRequest = components['schemas']['UpdateTransactionRequest'];

export type CreateCategoryRequest = components['schemas']['CreateCategoryRequest'];
export type UpdateCategoryRequest = components['schemas']['UpdateCategoryRequest'];

// Account API functions
export async function fetchAccounts(): Promise<AccountListResponse> {
  const response = await api.get<AccountListResponse>('/api/v1/accounts');
  return response.data;
}

export async function fetchAccount(id: string): Promise<AccountResponse> {
  const response = await api.get<AccountResponse>(`/api/v1/accounts/${id}`);
  return response.data;
}

export async function createCheckingAccount(
  data: CreateCheckingAccountRequest,
): Promise<AccountResponse> {
  const response = await api.post<AccountResponse>('/api/v1/accounts/checking', data);
  return response.data;
}

export async function createSavingsAccount(
  data: CreateSavingsAccountRequest,
): Promise<AccountResponse> {
  const response = await api.post<AccountResponse>('/api/v1/accounts/savings', data);
  return response.data;
}

export async function createCreditCardAccount(
  data: CreateCreditCardAccountRequest,
): Promise<AccountResponse> {
  const response = await api.post<AccountResponse>('/api/v1/accounts/credit-card', data);
  return response.data;
}

export async function createLoanAccount(data: CreateLoanAccountRequest): Promise<AccountResponse> {
  const response = await api.post<AccountResponse>('/api/v1/accounts/loan', data);
  return response.data;
}

export async function createBrokerageAccount(
  data: CreateBrokerageAccountRequest,
): Promise<AccountResponse> {
  const response = await api.post<AccountResponse>('/api/v1/accounts/brokerage', data);
  return response.data;
}

export async function createIraAccount(data: CreateIraAccountRequest): Promise<AccountResponse> {
  const response = await api.post<AccountResponse>('/api/v1/accounts/ira', data);
  return response.data;
}

export async function createRewardsAccount(
  data: CreateRewardsAccountRequest,
): Promise<AccountResponse> {
  const response = await api.post<AccountResponse>('/api/v1/accounts/rewards', data);
  return response.data;
}

export async function updateAccount(
  id: string,
  data: UpdateAccountRequest,
): Promise<AccountResponse> {
  const response = await api.patch<AccountResponse>(`/api/v1/accounts/${id}`, data);
  return response.data;
}

export async function deleteAccount(id: string): Promise<void> {
  await api.delete(`/api/v1/accounts/${id}`);
}

// Transaction API functions
export async function fetchTransactions(accountId?: string): Promise<TransactionListResponse> {
  const params = accountId ? { account_id: accountId } : undefined;
  const response = await api.get<TransactionListResponse>('/api/v1/transactions', { params });
  return response.data;
}

export async function fetchTransaction(id: string): Promise<TransactionResponse> {
  const response = await api.get<TransactionResponse>(`/api/v1/transactions/${id}`);
  return response.data;
}

export async function createTransaction(
  data: CreateTransactionRequest,
): Promise<TransactionResponse> {
  const response = await api.post<TransactionResponse>('/api/v1/transactions', data);
  return response.data;
}

export async function updateTransaction(
  id: string,
  data: UpdateTransactionRequest,
): Promise<TransactionResponse> {
  const response = await api.patch<TransactionResponse>(`/api/v1/transactions/${id}`, data);
  return response.data;
}

export async function deleteTransaction(id: string): Promise<void> {
  await api.delete(`/api/v1/transactions/${id}`);
}

// Category API functions
export async function fetchCategories(): Promise<CategoryListResponse> {
  const response = await api.get<CategoryListResponse>('/api/v1/categories');
  return response.data;
}

export async function fetchCategoryTree(): Promise<CategoryTreeResponse> {
  const response = await api.get<CategoryTreeResponse>('/api/v1/categories/tree');
  return response.data;
}

export async function createCategory(data: CreateCategoryRequest): Promise<CategoryResponse> {
  const response = await api.post<CategoryResponse>('/api/v1/categories', data);
  return response.data;
}

export async function updateCategory(
  id: string,
  data: UpdateCategoryRequest,
): Promise<CategoryResponse> {
  const response = await api.patch<CategoryResponse>(`/api/v1/categories/${id}`, data);
  return response.data;
}

export async function deleteCategory(id: string): Promise<void> {
  await api.delete(`/api/v1/categories/${id}`);
}

// Payee API functions - Placeholder for Phase 15+
// Backend doesn't have payee endpoints yet, but we'll add placeholders
// export async function fetchPayees(): Promise<PayeeListResponse> {
//   const response = await api.get<PayeeListResponse>('/api/v1/payees');
//   return response.data;
// }
