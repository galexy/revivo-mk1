/**
 * MSW request handlers for API mocking in tests.
 * Matches endpoints defined in api-client.ts.
 */
import { http, HttpResponse } from 'msw';
import {
  mockAccount,
  mockAccountsList,
  mockCategoriesList,
  mockCategoryTree,
  mockTokenResponse,
  mockUserProfile,
} from './fixtures';

const baseURL = 'http://localhost:8000';

export const handlers = [
  // Auth endpoints
  http.post(`${baseURL}/auth/token`, () => {
    return HttpResponse.json(mockTokenResponse);
  }),

  http.post(`${baseURL}/auth/refresh`, () => {
    return HttpResponse.json(mockTokenResponse);
  }),

  http.get(`${baseURL}/auth/me`, () => {
    return HttpResponse.json(mockUserProfile);
  }),

  http.post(`${baseURL}/auth/logout`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Account endpoints
  http.get(`${baseURL}/api/v1/accounts`, () => {
    return HttpResponse.json(mockAccountsList);
  }),

  http.get(`${baseURL}/api/v1/accounts/:accountId`, ({ params }) => {
    const { accountId } = params;
    // Return first mock account, real ID doesn't matter for unit tests
    return HttpResponse.json({ ...mockAccount, id: accountId as string });
  }),

  http.post(`${baseURL}/api/v1/accounts/checking`, () => {
    return HttpResponse.json(mockAccount);
  }),

  http.post(`${baseURL}/api/v1/accounts/savings`, () => {
    return HttpResponse.json(mockAccount);
  }),

  http.post(`${baseURL}/api/v1/accounts/credit-card`, () => {
    return HttpResponse.json(mockAccount);
  }),

  http.patch(`${baseURL}/api/v1/accounts/:accountId`, ({ params }) => {
    return HttpResponse.json({ ...mockAccount, id: params.accountId as string });
  }),

  http.delete(`${baseURL}/api/v1/accounts/:accountId`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Category endpoints
  http.get(`${baseURL}/api/v1/categories`, () => {
    return HttpResponse.json(mockCategoriesList);
  }),

  http.get(`${baseURL}/api/v1/categories/tree`, () => {
    return HttpResponse.json(mockCategoryTree);
  }),

  http.post(`${baseURL}/api/v1/categories`, () => {
    return HttpResponse.json(mockCategoriesList.categories[0]);
  }),

  http.patch(`${baseURL}/api/v1/categories/:categoryId`, ({ params }) => {
    return HttpResponse.json({
      ...mockCategoriesList.categories[0],
      id: params.categoryId as string,
    });
  }),

  http.delete(`${baseURL}/api/v1/categories/:categoryId`, () => {
    return new HttpResponse(null, { status: 204 });
  }),
];
