export interface UserProfile {
  user_id: string;
  email: string;
  display_name: string;
  email_verified: boolean;
  created_at: string;
  household: {
    id: string;
    name: string;
    is_owner: boolean;
  };
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
}

export interface RegisterResponse {
  message: string;
  user_id: string;
  email: string;
}

export interface VerifyEmailResponse {
  message: string;
  user_id: string;
  email: string;
}

export interface AuthError {
  detail: string;
}
