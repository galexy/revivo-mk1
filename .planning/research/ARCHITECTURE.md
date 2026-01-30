# Architecture Research: Personal Finance Platform

**Domain:** Personal Finance Management with DDD + Clean Architecture
**Researched:** 2026-01-29
**Confidence:** HIGH (verified patterns from multiple authoritative sources)

## Executive Summary

This document defines the architectural structure for a personal finance platform built with Domain-Driven Design (DDD) and Clean Architecture (hexagonal/onion). The architecture enables multi-interface support (Web UI, REST API, CLI, AI) while keeping the domain layer completely isolated from infrastructure concerns.

Key architectural decisions:
- **Hexagonal Architecture** as the foundation (most pragmatic for multi-interface support)
- **Double-entry bookkeeping model** for accurate financial tracking
- **Bounded contexts** separating Accounts, Transactions, Budgeting, and Bank Sync
- **CQRS for read-heavy operations** without full event sourcing initially
- **Data Mapper pattern** with repository abstraction for persistence

---

## Recommended Architecture

### System Overview (Hexagonal/Ports & Adapters)

```
                              ┌─────────────────────────────────────────────────────────────┐
                              │                    PRIMARY ADAPTERS                          │
                              │            (Driving - Initiate Interactions)                 │
                              │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
                              │   │  Web UI  │  │ REST API │  │   CLI    │  │ AI Agent │   │
                              │   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
                              └────────┼─────────────┼─────────────┼─────────────┼─────────┘
                                       │             │             │             │
                                       ▼             ▼             ▼             ▼
                              ┌─────────────────────────────────────────────────────────────┐
                              │                    PRIMARY PORTS                             │
                              │              (Interfaces for Use Cases)                      │
                              │   ┌─────────────────────────────────────────────────────┐   │
                              │   │  IAccountService  ITransactionService  IBudgetService│   │
                              │   │  IReportingService  IBankSyncService  IReconciliation│   │
                              │   └─────────────────────────────────────────────────────┘   │
                              └─────────────────────────────────────────────────────────────┘
                                                         │
                                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      APPLICATION LAYER                                             │
│                              (Use Cases / Application Services)                                    │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│   │ CreateAccount   │  │ RecordTransfer  │  │ SetBudget       │  │ SyncBankAccount │             │
│   │ GetAccountBalance│  │ CategorizeSpend │  │ CheckBudgetAlert│  │ ReconcileTxns   │             │
│   │ CloseAccount    │  │ SplitTransaction│  │ GenerateReport  │  │ RefreshBalances │             │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                         │                                                          │
│                              Orchestrates domain objects,                                          │
│                              coordinates transactions                                              │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                         │
                                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       DOMAIN LAYER                                                 │
│                        (Entities, Value Objects, Aggregates, Domain Services)                      │
│                                                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────┐    │
│   │                              AGGREGATES                                                   │    │
│   │   ┌───────────────┐  ┌───────────────────┐  ┌────────────┐  ┌─────────────────────┐    │    │
│   │   │   Account     │  │   Transaction     │  │   Budget   │  │   BankConnection    │    │    │
│   │   │   (root)      │  │   (root)          │  │   (root)   │  │   (root)            │    │    │
│   │   │   - Balance   │  │   - Entries[]     │  │   - Limits │  │   - AccessToken     │    │    │
│   │   │   - Type      │  │   - Category      │  │   - Period │  │   - Institution     │    │    │
│   │   │   - Currency  │  │   - Status        │  │   - Alerts │  │   - LastSync        │    │    │
│   │   └───────────────┘  └───────────────────┘  └────────────┘  └─────────────────────┘    │    │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────┐    │
│   │                           VALUE OBJECTS                                                   │    │
│   │   Money | AccountId | TransactionId | CategoryId | DateRange | Currency | Percentage    │    │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────┐    │
│   │                           DOMAIN SERVICES                                                 │    │
│   │   TransferService | ReconciliationService | BudgetCalculationService                     │    │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────┐    │
│   │                           DOMAIN EVENTS                                                   │    │
│   │   AccountCreated | TransactionRecorded | BudgetExceeded | BankSyncCompleted              │    │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                         │
                                                         ▼
                              ┌─────────────────────────────────────────────────────────────┐
                              │                   SECONDARY PORTS                            │
                              │            (Interfaces for Infrastructure)                   │
                              │   ┌─────────────────────────────────────────────────────┐   │
                              │   │  IAccountRepository  ITransactionRepository          │   │
                              │   │  IBudgetRepository   IBankSyncRepository             │   │
                              │   │  IEventPublisher     IJobScheduler                   │   │
                              │   └─────────────────────────────────────────────────────┘   │
                              └─────────────────────────────────────────────────────────────┘
                                                         │
                                                         ▼
                              ┌─────────────────────────────────────────────────────────────┐
                              │                  SECONDARY ADAPTERS                          │
                              │             (Driven - Called by Application)                 │
                              │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
                              │   │PostgreSQL│  │  Redis   │  │  Plaid   │  │  BullMQ  │   │
                              │   │ Repos    │  │  Cache   │  │ Adapter  │  │  Jobs    │   │
                              │   └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
                              │   ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
                              │   │  OTel    │  │  Email   │  │   S3     │                 │
                              │   │ Metrics  │  │ Sender   │  │ Storage  │                 │
                              │   └──────────┘  └──────────┘  └──────────┘                 │
                              └─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Depends On | Examples |
|-------|----------------|------------|----------|
| **Primary Adapters** | Convert external input to application calls | Application Layer (via ports) | Express controllers, CLI commands, WebSocket handlers |
| **Application Layer** | Orchestrate use cases, coordinate transactions | Domain Layer | CreateAccountUseCase, RecordTransferUseCase |
| **Domain Layer** | Core business logic, invariants, rules | Nothing (pure) | Account, Transaction, Money, TransferService |
| **Secondary Adapters** | Implement infrastructure interfaces | Infrastructure concerns | PostgresAccountRepository, PlaidBankAdapter |

### Dependency Rule

**All dependencies point inward.** The domain layer has zero dependencies on infrastructure, frameworks, or external libraries (except standard library types). This is enforced through:

1. Ports (interfaces) defined in domain/application layers
2. Adapters implementing those interfaces in infrastructure layer
3. Dependency injection wiring at composition root

---

## Recommended Project Structure

```
src/
├── domain/                          # Pure business logic (no dependencies)
│   ├── accounts/                    # Account bounded context
│   │   ├── entities/
│   │   │   └── Account.ts           # Account aggregate root
│   │   ├── value-objects/
│   │   │   ├── AccountId.ts
│   │   │   ├── AccountType.ts
│   │   │   └── Balance.ts
│   │   ├── events/
│   │   │   ├── AccountCreated.ts
│   │   │   └── AccountClosed.ts
│   │   ├── services/
│   │   │   └── AccountValidationService.ts
│   │   └── ports/
│   │       └── IAccountRepository.ts
│   │
│   ├── transactions/                # Transaction bounded context
│   │   ├── entities/
│   │   │   ├── Transaction.ts       # Transaction aggregate root
│   │   │   └── TransactionEntry.ts  # Entity (part of aggregate)
│   │   ├── value-objects/
│   │   │   ├── TransactionId.ts
│   │   │   ├── Money.ts             # Immutable money value object
│   │   │   ├── Currency.ts
│   │   │   └── CategoryId.ts
│   │   ├── events/
│   │   │   ├── TransactionRecorded.ts
│   │   │   └── TransactionCategorized.ts
│   │   ├── services/
│   │   │   └── TransferService.ts   # Domain service for transfers
│   │   └── ports/
│   │       └── ITransactionRepository.ts
│   │
│   ├── budgeting/                   # Budget bounded context
│   │   ├── entities/
│   │   │   └── Budget.ts
│   │   ├── value-objects/
│   │   │   ├── BudgetPeriod.ts
│   │   │   └── SpendingLimit.ts
│   │   ├── events/
│   │   │   └── BudgetExceeded.ts
│   │   └── ports/
│   │       └── IBudgetRepository.ts
│   │
│   ├── bank-sync/                   # Bank synchronization bounded context
│   │   ├── entities/
│   │   │   └── BankConnection.ts
│   │   ├── value-objects/
│   │   │   ├── PlaidItemId.ts
│   │   │   └── AccessToken.ts
│   │   ├── events/
│   │   │   └── BankSyncCompleted.ts
│   │   ├── services/
│   │   │   └── ReconciliationService.ts
│   │   └── ports/
│   │       ├── IBankConnectionRepository.ts
│   │       └── IBankDataProvider.ts  # Abstract interface for Plaid
│   │
│   └── shared/                      # Cross-cutting domain concerns
│       ├── value-objects/
│       │   ├── UserId.ts
│       │   ├── DateRange.ts
│       │   └── Percentage.ts
│       ├── Entity.ts                # Base entity class
│       ├── AggregateRoot.ts         # Base aggregate root
│       ├── ValueObject.ts           # Base value object
│       └── DomainEvent.ts           # Base domain event
│
├── application/                     # Use cases / application services
│   ├── accounts/
│   │   ├── CreateAccountUseCase.ts
│   │   ├── GetAccountBalanceUseCase.ts
│   │   └── CloseAccountUseCase.ts
│   ├── transactions/
│   │   ├── RecordTransactionUseCase.ts
│   │   ├── RecordTransferUseCase.ts
│   │   ├── SplitTransactionUseCase.ts
│   │   └── CategorizeTransactionUseCase.ts
│   ├── budgeting/
│   │   ├── SetBudgetUseCase.ts
│   │   └── CheckBudgetStatusUseCase.ts
│   ├── bank-sync/
│   │   ├── InitiateBankLinkUseCase.ts
│   │   ├── SyncTransactionsUseCase.ts
│   │   └── ReconcileTransactionsUseCase.ts
│   ├── reporting/
│   │   ├── GenerateSpendingReportUseCase.ts
│   │   └── GenerateNetWorthReportUseCase.ts
│   └── ports/                       # Application-level ports
│       ├── IUnitOfWork.ts
│       ├── IEventPublisher.ts
│       └── IJobScheduler.ts
│
├── infrastructure/                  # Adapters / implementations
│   ├── persistence/
│   │   ├── postgres/
│   │   │   ├── PostgresAccountRepository.ts
│   │   │   ├── PostgresTransactionRepository.ts
│   │   │   ├── PostgresBudgetRepository.ts
│   │   │   ├── PostgresBankConnectionRepository.ts
│   │   │   └── mappers/             # Data mappers
│   │   │       ├── AccountMapper.ts
│   │   │       ├── TransactionMapper.ts
│   │   │       └── BudgetMapper.ts
│   │   ├── migrations/
│   │   └── PostgresUnitOfWork.ts
│   │
│   ├── external/
│   │   ├── plaid/
│   │   │   ├── PlaidBankDataProvider.ts
│   │   │   ├── PlaidWebhookHandler.ts
│   │   │   └── PlaidTransactionMapper.ts
│   │   └── email/
│   │       └── SendGridEmailService.ts
│   │
│   ├── jobs/
│   │   ├── BullMQJobScheduler.ts
│   │   ├── workers/
│   │   │   ├── SyncBankAccountsWorker.ts
│   │   │   ├── CreateRecurringTransactionsWorker.ts
│   │   │   └── SendBudgetAlertsWorker.ts
│   │   └── queues.ts
│   │
│   ├── cache/
│   │   └── RedisCache.ts
│   │
│   └── observability/
│       ├── OpenTelemetrySetup.ts
│       └── MetricsCollector.ts
│
├── interfaces/                      # Primary adapters (entry points)
│   ├── http/
│   │   ├── express/
│   │   │   ├── app.ts
│   │   │   ├── middleware/
│   │   │   │   ├── authMiddleware.ts
│   │   │   │   ├── errorHandler.ts
│   │   │   │   └── requestId.ts
│   │   │   ├── controllers/
│   │   │   │   ├── AccountController.ts
│   │   │   │   ├── TransactionController.ts
│   │   │   │   ├── BudgetController.ts
│   │   │   │   └── BankSyncController.ts
│   │   │   ├── routes/
│   │   │   └── dto/                 # Request/Response DTOs
│   │   │       ├── CreateAccountRequest.ts
│   │   │       ├── TransactionResponse.ts
│   │   │       └── index.ts
│   │   └── webhooks/
│   │       └── PlaidWebhookController.ts
│   │
│   ├── cli/
│   │   ├── commands/
│   │   │   ├── importTransactions.ts
│   │   │   ├── generateReport.ts
│   │   │   └── syncAccounts.ts
│   │   └── index.ts
│   │
│   └── ai/                          # AI agent interface
│       ├── tools/
│       │   ├── getSpendingSummary.ts
│       │   ├── categorizeTransaction.ts
│       │   └── setBudgetAlert.ts
│       └── AgentInterface.ts
│
├── config/
│   ├── container.ts                 # DI container setup
│   ├── database.ts
│   ├── plaid.ts
│   └── environment.ts
│
└── main.ts                          # Composition root
```

### Structure Rationale

- **domain/**: Organized by bounded context, each with entities, value objects, events, services, and repository ports. No external dependencies allowed.
- **application/**: Use cases organized by bounded context. Each use case is a single class with one public method.
- **infrastructure/**: All external integrations. Implements domain/application ports. Can have any dependencies.
- **interfaces/**: Primary adapters for different entry points (HTTP, CLI, AI). Translates external requests to application use case calls.
- **config/**: Wiring and configuration. Composition root assembles the application.

---

## Architectural Patterns

### Pattern 1: Double-Entry Transaction Model

**What:** Every financial transaction consists of two or more entries that must balance (debits = credits). This models real money movement.

**When to use:** For all financial transactions - expenses, income, transfers, splits.

**Trade-offs:**
- (+) Always balanced, catches errors
- (+) Transfers are natural (not special cases)
- (+) Audit trail built-in
- (-) More complex than single-entry
- (-) Requires understanding accounting concepts

**Example:**
```typescript
// domain/transactions/entities/Transaction.ts
export class Transaction extends AggregateRoot<TransactionId> {
  private readonly entries: TransactionEntry[];
  private readonly date: Date;
  private readonly description: string;
  private status: TransactionStatus;

  private constructor(props: TransactionProps) {
    super(props.id);
    this.entries = props.entries;
    this.date = props.date;
    this.description = props.description;
    this.status = props.status;
    this.validateBalance();
  }

  private validateBalance(): void {
    const sum = this.entries.reduce(
      (acc, entry) => acc.add(entry.amount),
      Money.zero(this.entries[0].amount.currency)
    );
    if (!sum.isZero()) {
      throw new TransactionNotBalancedError(sum);
    }
  }

  static createExpense(
    fromAccount: AccountId,
    categoryAccount: AccountId,
    amount: Money,
    description: string
  ): Transaction {
    return new Transaction({
      id: TransactionId.generate(),
      entries: [
        TransactionEntry.debit(categoryAccount, amount),   // Expense increases
        TransactionEntry.credit(fromAccount, amount),      // Asset decreases
      ],
      date: new Date(),
      description,
      status: TransactionStatus.Pending,
    });
  }

  static createTransfer(
    fromAccount: AccountId,
    toAccount: AccountId,
    amount: Money,
    description: string
  ): Transaction {
    return new Transaction({
      id: TransactionId.generate(),
      entries: [
        TransactionEntry.debit(toAccount, amount),   // Destination increases
        TransactionEntry.credit(fromAccount, amount), // Source decreases
      ],
      date: new Date(),
      description,
      status: TransactionStatus.Pending,
    });
  }

  // Split transaction across multiple categories
  static createSplitExpense(
    fromAccount: AccountId,
    splits: Array<{ categoryAccount: AccountId; amount: Money }>,
    description: string
  ): Transaction {
    const entries: TransactionEntry[] = [];
    let totalAmount = Money.zero(splits[0].amount.currency);

    for (const split of splits) {
      entries.push(TransactionEntry.debit(split.categoryAccount, split.amount));
      totalAmount = totalAmount.add(split.amount);
    }
    entries.push(TransactionEntry.credit(fromAccount, totalAmount));

    return new Transaction({
      id: TransactionId.generate(),
      entries,
      date: new Date(),
      description,
      status: TransactionStatus.Pending,
    });
  }
}

// domain/transactions/entities/TransactionEntry.ts
export class TransactionEntry extends Entity<TransactionEntryId> {
  readonly accountId: AccountId;
  readonly amount: Money;  // Positive = debit, Negative = credit
  readonly entryType: EntryType;

  static debit(accountId: AccountId, amount: Money): TransactionEntry {
    return new TransactionEntry({
      id: TransactionEntryId.generate(),
      accountId,
      amount: amount.abs(),
      entryType: EntryType.Debit,
    });
  }

  static credit(accountId: AccountId, amount: Money): TransactionEntry {
    return new TransactionEntry({
      id: TransactionEntryId.generate(),
      accountId,
      amount: amount.abs().negate(),
      entryType: EntryType.Credit,
    });
  }
}
```

### Pattern 2: Money Value Object

**What:** Immutable value object representing monetary amounts with currency. Prevents floating-point errors and currency mixing.

**When to use:** All monetary calculations. Never use raw numbers for money.

**Trade-offs:**
- (+) Prevents floating-point errors
- (+) Currency-safe (can't accidentally mix USD and EUR)
- (+) Immutable (thread-safe, predictable)
- (-) More verbose than raw numbers
- (-) Requires careful serialization

**Example:**
```typescript
// domain/transactions/value-objects/Money.ts
export class Money extends ValueObject<MoneyProps> {
  private readonly amountInCents: number;  // Store as integer cents
  private readonly currency: Currency;

  private constructor(amountInCents: number, currency: Currency) {
    super({ amountInCents, currency });
    this.amountInCents = amountInCents;
    this.currency = currency;
  }

  static fromCents(cents: number, currency: Currency): Money {
    if (!Number.isInteger(cents)) {
      throw new InvalidMoneyError('Amount in cents must be an integer');
    }
    return new Money(cents, currency);
  }

  static fromDollars(dollars: number, currency: Currency): Money {
    const cents = Math.round(dollars * 100);
    return new Money(cents, currency);
  }

  static zero(currency: Currency): Money {
    return new Money(0, currency);
  }

  add(other: Money): Money {
    this.assertSameCurrency(other);
    return new Money(this.amountInCents + other.amountInCents, this.currency);
  }

  subtract(other: Money): Money {
    this.assertSameCurrency(other);
    return new Money(this.amountInCents - other.amountInCents, this.currency);
  }

  multiply(factor: number): Money {
    return new Money(Math.round(this.amountInCents * factor), this.currency);
  }

  negate(): Money {
    return new Money(-this.amountInCents, this.currency);
  }

  abs(): Money {
    return new Money(Math.abs(this.amountInCents), this.currency);
  }

  isZero(): boolean {
    return this.amountInCents === 0;
  }

  isPositive(): boolean {
    return this.amountInCents > 0;
  }

  isNegative(): boolean {
    return this.amountInCents < 0;
  }

  private assertSameCurrency(other: Money): void {
    if (!this.currency.equals(other.currency)) {
      throw new CurrencyMismatchError(this.currency, other.currency);
    }
  }

  toCents(): number {
    return this.amountInCents;
  }

  toDollars(): number {
    return this.amountInCents / 100;
  }

  format(): string {
    return this.currency.format(this.amountInCents);
  }
}
```

### Pattern 3: Repository with Data Mapper

**What:** Repository provides collection-like interface for aggregates. Data Mapper handles translation between domain objects and persistence format.

**When to use:** All aggregate persistence. Never let domain objects know about database schema.

**Trade-offs:**
- (+) Domain model independent of persistence
- (+) Can change database without changing domain
- (+) Enables proper unit testing with fakes
- (-) More code than Active Record
- (-) Mapping logic can become complex

**Example:**
```typescript
// domain/accounts/ports/IAccountRepository.ts
export interface IAccountRepository {
  findById(id: AccountId): Promise<Account | null>;
  findByUserId(userId: UserId): Promise<Account[]>;
  save(account: Account): Promise<void>;
  delete(id: AccountId): Promise<void>;
}

// infrastructure/persistence/postgres/mappers/AccountMapper.ts
export class AccountMapper {
  static toDomain(raw: AccountRow): Account {
    return Account.reconstitute({
      id: AccountId.from(raw.id),
      userId: UserId.from(raw.user_id),
      name: raw.name,
      type: AccountType.from(raw.type),
      currency: Currency.from(raw.currency),
      balance: Money.fromCents(raw.balance_cents, Currency.from(raw.currency)),
      isActive: raw.is_active,
      createdAt: raw.created_at,
      updatedAt: raw.updated_at,
    });
  }

  static toPersistence(account: Account): AccountRow {
    return {
      id: account.id.value,
      user_id: account.userId.value,
      name: account.name,
      type: account.type.value,
      currency: account.currency.code,
      balance_cents: account.balance.toCents(),
      is_active: account.isActive,
      created_at: account.createdAt,
      updated_at: account.updatedAt,
    };
  }
}

// infrastructure/persistence/postgres/PostgresAccountRepository.ts
export class PostgresAccountRepository implements IAccountRepository {
  constructor(private readonly db: DatabaseClient) {}

  async findById(id: AccountId): Promise<Account | null> {
    const row = await this.db.query<AccountRow>(
      'SELECT * FROM accounts WHERE id = $1',
      [id.value]
    );
    return row ? AccountMapper.toDomain(row) : null;
  }

  async save(account: Account): Promise<void> {
    const data = AccountMapper.toPersistence(account);
    await this.db.query(
      `INSERT INTO accounts (id, user_id, name, type, currency, balance_cents, is_active, created_at, updated_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       ON CONFLICT (id) DO UPDATE SET
         name = $3, type = $4, balance_cents = $6, is_active = $7, updated_at = $9`,
      [data.id, data.user_id, data.name, data.type, data.currency,
       data.balance_cents, data.is_active, data.created_at, data.updated_at]
    );
  }
}
```

### Pattern 4: Use Case / Application Service

**What:** Each use case is a single class that orchestrates domain objects and infrastructure to accomplish a business goal.

**When to use:** For every user-facing operation. Use cases are the entry point from interfaces to domain.

**Trade-offs:**
- (+) Clear, testable business operations
- (+) Transaction boundaries are explicit
- (+) Easy to understand what the system does
- (-) Can lead to many small classes
- (-) Must avoid putting domain logic here

**Example:**
```typescript
// application/transactions/RecordTransferUseCase.ts
export class RecordTransferUseCase {
  constructor(
    private readonly accountRepository: IAccountRepository,
    private readonly transactionRepository: ITransactionRepository,
    private readonly unitOfWork: IUnitOfWork,
    private readonly eventPublisher: IEventPublisher
  ) {}

  async execute(request: RecordTransferRequest): Promise<RecordTransferResponse> {
    const { fromAccountId, toAccountId, amount, description } = request;

    // Load aggregates
    const fromAccount = await this.accountRepository.findById(
      AccountId.from(fromAccountId)
    );
    if (!fromAccount) {
      throw new AccountNotFoundError(fromAccountId);
    }

    const toAccount = await this.accountRepository.findById(
      AccountId.from(toAccountId)
    );
    if (!toAccount) {
      throw new AccountNotFoundError(toAccountId);
    }

    // Validate business rules
    const transferAmount = Money.fromCents(amount.cents, Currency.from(amount.currency));
    if (!fromAccount.canWithdraw(transferAmount)) {
      throw new InsufficientFundsError(fromAccountId, transferAmount);
    }

    // Create transaction (domain logic)
    const transaction = Transaction.createTransfer(
      fromAccount.id,
      toAccount.id,
      transferAmount,
      description
    );

    // Update account balances
    fromAccount.debit(transferAmount);
    toAccount.credit(transferAmount);

    // Persist within transaction
    await this.unitOfWork.executeInTransaction(async () => {
      await this.transactionRepository.save(transaction);
      await this.accountRepository.save(fromAccount);
      await this.accountRepository.save(toAccount);
    });

    // Publish domain events
    await this.eventPublisher.publish(transaction.pullDomainEvents());

    return {
      transactionId: transaction.id.value,
      status: 'completed',
    };
  }
}
```

### Pattern 5: Plaid Integration via Port/Adapter

**What:** Abstract bank data access behind a port interface, implement with Plaid adapter. Domain never knows about Plaid.

**When to use:** All external bank integrations. The port defines what we need; the adapter provides it.

**Trade-offs:**
- (+) Can swap Plaid for another provider
- (+) Domain stays clean
- (+) Easy to mock for testing
- (-) Must map Plaid's model to ours
- (-) Webhook handling adds complexity

**Example:**
```typescript
// domain/bank-sync/ports/IBankDataProvider.ts
export interface IBankDataProvider {
  createLinkToken(userId: UserId): Promise<LinkToken>;
  exchangePublicToken(publicToken: string): Promise<AccessToken>;
  getAccounts(accessToken: AccessToken): Promise<BankAccountData[]>;
  getTransactions(
    accessToken: AccessToken,
    options: TransactionFetchOptions
  ): Promise<BankTransactionData[]>;
  syncTransactions(
    accessToken: AccessToken,
    cursor?: string
  ): Promise<TransactionSyncResult>;
}

export interface BankAccountData {
  externalId: string;
  name: string;
  type: string;
  subtype: string;
  balanceCurrent: number;
  balanceAvailable: number | null;
  currency: string;
  institutionId: string;
  institutionName: string;
}

export interface BankTransactionData {
  externalId: string;
  accountExternalId: string;
  amount: number;
  currency: string;
  date: Date;
  name: string;
  merchantName: string | null;
  category: string[];
  pending: boolean;
}

// infrastructure/external/plaid/PlaidBankDataProvider.ts
export class PlaidBankDataProvider implements IBankDataProvider {
  private readonly client: PlaidApi;

  constructor(config: PlaidConfig) {
    const configuration = new Configuration({
      basePath: PlaidEnvironments[config.environment],
      baseOptions: {
        headers: {
          'PLAID-CLIENT-ID': config.clientId,
          'PLAID-SECRET': config.secret,
        },
      },
    });
    this.client = new PlaidApi(configuration);
  }

  async createLinkToken(userId: UserId): Promise<LinkToken> {
    const response = await this.client.linkTokenCreate({
      user: { client_user_id: userId.value },
      client_name: 'Finance App',
      products: [Products.Transactions],
      country_codes: [CountryCode.Us],
      language: 'en',
    });
    return LinkToken.from(response.data.link_token);
  }

  async getTransactions(
    accessToken: AccessToken,
    options: TransactionFetchOptions
  ): Promise<BankTransactionData[]> {
    const response = await this.client.transactionsGet({
      access_token: accessToken.value,
      start_date: options.startDate.toISOString().split('T')[0],
      end_date: options.endDate.toISOString().split('T')[0],
    });

    return response.data.transactions.map(this.mapTransaction);
  }

  private mapTransaction(plaidTxn: Transaction): BankTransactionData {
    return {
      externalId: plaidTxn.transaction_id,
      accountExternalId: plaidTxn.account_id,
      amount: plaidTxn.amount,
      currency: plaidTxn.iso_currency_code || 'USD',
      date: new Date(plaidTxn.date),
      name: plaidTxn.name,
      merchantName: plaidTxn.merchant_name,
      category: plaidTxn.category || [],
      pending: plaidTxn.pending,
    };
  }
}
```

---

## Data Flow

### Request Flow (Web API Example)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              REQUEST FLOW                                     │
└──────────────────────────────────────────────────────────────────────────────┘

  HTTP POST /api/transactions/transfer
       │
       ▼
┌──────────────────┐
│ Express Router   │  Route matching, basic validation
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Auth Middleware  │  Verify JWT, extract userId
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Controller       │  Parse request body, validate DTO
│ (Primary Adapter)│  Convert to use case request
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Use Case         │  Load aggregates via repositories
│ (Application)    │  Coordinate domain operations
│                  │  Manage transaction boundaries
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Domain           │  Execute business rules
│ (Transaction,    │  Validate invariants
│  Account, Money) │  Generate domain events
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Repository       │  Map domain → persistence
│ (Secondary       │  Execute SQL
│  Adapter)        │  Map persistence → domain
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Event Publisher  │  Dispatch domain events
│ (Secondary       │  (async, may trigger jobs)
│  Adapter)        │
└──────────────────┘
```

### Bank Sync Data Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           BANK SYNC FLOW                                      │
└──────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │ 1. LINK FLOW (User connects bank)                               │
  └─────────────────────────────────────────────────────────────────┘

  User clicks "Connect Bank"
       │
       ▼
  Frontend requests link_token
       │
       ▼
  Backend → Plaid: linkTokenCreate()
       │
       ▼
  Frontend opens Plaid Link with token
       │
       ▼
  User authenticates with bank in Plaid UI
       │
       ▼
  Plaid returns public_token to frontend
       │
       ▼
  Frontend sends public_token to backend
       │
       ▼
  Backend → Plaid: exchangePublicToken()
       │
       ▼
  Store encrypted access_token in BankConnection
       │
       ▼
  Trigger initial sync


  ┌─────────────────────────────────────────────────────────────────┐
  │ 2. SYNC FLOW (Fetch transactions)                               │
  └─────────────────────────────────────────────────────────────────┘

  Webhook or Scheduled Job triggers sync
       │
       ▼
  Load BankConnection with access_token
       │
       ▼
  Call IBankDataProvider.syncTransactions(cursor)
       │
       ▼
  Plaid returns: added[], modified[], removed[], nextCursor
       │
       ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ RECONCILIATION                                                   │
  │                                                                  │
  │  For each added transaction:                                     │
  │    → Match to existing? Update external_id                       │
  │    → No match? Create new pending Transaction                    │
  │                                                                  │
  │  For each modified transaction:                                  │
  │    → Find by external_id                                         │
  │    → Update amount/date/status                                   │
  │                                                                  │
  │  For each removed transaction:                                   │
  │    → Find by external_id                                         │
  │    → Mark as void or delete                                      │
  └─────────────────────────────────────────────────────────────────┘
       │
       ▼
  Update BankConnection.lastSyncCursor
       │
       ▼
  Publish BankSyncCompleted event
```

### Background Job Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         BACKGROUND JOB FLOW                                   │
└──────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │ Job Types                                                        │
  │                                                                  │
  │ 1. SCHEDULED (Repeatable)                                        │
  │    - Sync all bank accounts (every 6 hours)                      │
  │    - Create recurring transactions (daily at midnight)           │
  │    - Generate spending summaries (weekly)                        │
  │                                                                  │
  │ 2. EVENT-TRIGGERED                                               │
  │    - Send budget alert (on BudgetExceeded event)                 │
  │    - Categorize transaction (on TransactionRecorded event)       │
  │                                                                  │
  │ 3. ON-DEMAND                                                     │
  │    - Force sync specific account                                 │
  │    - Generate report                                             │
  └─────────────────────────────────────────────────────────────────┘

                    BullMQ Architecture

  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   Queue:    │     │   Queue:    │     │   Queue:    │
  │  bank-sync  │     │   alerts    │     │  recurring  │
  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │      Redis      │
                    │  (Job Storage)  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │   Worker:    │   │   Worker:    │   │   Worker:    │
  │  BankSync    │   │   Alerts     │   │  Recurring   │
  │              │   │              │   │              │
  │ Concurrency:3│   │ Concurrency:5│   │ Concurrency:1│
  └──────────────┘   └──────────────┘   └──────────────┘
```

---

## Bounded Contexts

### Context Map

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                             BOUNDED CONTEXTS                                    │
└────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                              CORE DOMAIN                                     │
  │  (Differentiating business capabilities - build carefully)                   │
  └─────────────────────────────────────────────────────────────────────────────┘

        ┌─────────────────┐                     ┌─────────────────┐
        │    ACCOUNTS     │◄────────────────────│  TRANSACTIONS   │
        │                 │   uses AccountId    │                 │
        │ - Account       │                     │ - Transaction   │
        │ - AccountType   │                     │ - Entry         │
        │ - Balance       │                     │ - Money         │
        │                 │                     │ - Category      │
        └────────┬────────┘                     └────────┬────────┘
                 │                                       │
                 │ AccountId                             │ TransactionSummary
                 ▼                                       ▼
        ┌─────────────────┐                     ┌─────────────────┐
        │   BUDGETING     │                     │   REPORTING     │
        │                 │                     │                 │
        │ - Budget        │◄────────────────────│ - SpendReport   │
        │ - SpendLimit    │   CategorySpending  │ - NetWorthSnap  │
        │ - BudgetPeriod  │                     │ - TrendAnalysis │
        └─────────────────┘                     └─────────────────┘


  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                            SUPPORTING DOMAIN                                 │
  │  (Necessary but not differentiating - can use established patterns)          │
  └─────────────────────────────────────────────────────────────────────────────┘

        ┌─────────────────┐
        │   BANK SYNC     │
        │                 │
        │ - BankConnection│───────────────────────► Plaid (External)
        │ - AccessToken   │
        │ - Reconciliation│────────► Transactions Context
        └─────────────────┘


  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                            GENERIC DOMAIN                                    │
  │  (Commodity - use off-the-shelf solutions)                                   │
  └─────────────────────────────────────────────────────────────────────────────┘

        ┌─────────────────┐         ┌─────────────────┐
        │ AUTHENTICATION  │         │  NOTIFICATIONS  │
        │                 │         │                 │
        │ (Use Auth0/     │         │ (Use SendGrid/  │
        │  Clerk/Supabase)│         │  Resend)        │
        └─────────────────┘         └─────────────────┘
```

### Context Relationships

| Upstream Context | Downstream Context | Relationship | Integration Pattern |
|------------------|-------------------|--------------|---------------------|
| Accounts | Transactions | Conformist | Transaction uses AccountId directly |
| Transactions | Budgeting | Published Language | TransactionRecorded event with category spending |
| Transactions | Reporting | Published Language | Query service reads transaction projections |
| Bank Sync | Transactions | Anti-Corruption Layer | Plaid transactions mapped to domain Transactions |
| Authentication | All | Open Host Service | JWT claims provide UserId |

### Key Insight: Same Term, Different Meaning

The term "Account" means different things in different contexts:

| Context | "Account" Means | Key Attributes |
|---------|-----------------|----------------|
| Accounts | Container for money (checking, savings, credit card) | Balance, Type, Currency |
| Bank Sync | External bank account linked via Plaid | ExternalId, AccessToken, Institution |
| Authentication | User identity | Email, Password, Roles |
| Transactions | Ledger account (asset, liability, expense) | AccountType, NormalBalance |

---

## CQRS Considerations

### Recommendation: Light CQRS Without Event Sourcing

For a personal finance app, **implement read/write separation at the service level without full event sourcing**. Here's why:

**Do use CQRS patterns:**
- Separate query services for reports (spending summaries, net worth)
- Denormalized read models for dashboard data
- Command handlers for writes, Query handlers for reads

**Don't use full Event Sourcing initially:**
- Audit requirements satisfied by transaction log + domain events
- Event sourcing adds significant complexity
- Rebuilding projections from events is overkill for typical PFM
- Can add later for specific contexts (e.g., investment portfolio tracking)

### Example: Light CQRS Structure

```typescript
// Commands (writes) - use full domain model
application/
├── commands/
│   ├── RecordTransactionCommand.ts
│   ├── CreateAccountCommand.ts
│   └── SetBudgetCommand.ts

// Queries (reads) - can bypass domain, use optimized reads
application/
├── queries/
│   ├── GetSpendingSummaryQuery.ts      // Reads from denormalized table
│   ├── GetAccountBalancesQuery.ts      // Direct SQL, no domain hydration
│   └── GetBudgetStatusQuery.ts         // Joins across tables

// Read models (denormalized for performance)
infrastructure/
├── read-models/
│   ├── SpendingSummaryProjection.ts    // Updated on TransactionRecorded
│   ├── AccountBalanceCache.ts          // Updated on balance changes
│   └── BudgetStatusMaterializedView.ts // PostgreSQL materialized view
```

### When to Consider Event Sourcing

Add event sourcing **later** for specific use cases:

| Use Case | Event Sourcing Value | Approach |
|----------|---------------------|----------|
| Audit trail | High - "show me history" | Store domain events, not just state |
| Investment tracking | High - need point-in-time values | Event source portfolio changes |
| Undo/redo | Medium - but rare in finance | Event sourcing enables replay |
| Analytics | Medium - can derive from events | Event store + projections |

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k users | Monolith is perfect. Single Postgres, single Node process. Don't optimize. |
| 1k-10k users | Add Redis caching for read-heavy queries (balances, summaries). Separate read replicas for reports. |
| 10k-100k users | Split background jobs to separate workers. Consider read model projections in Redis. |
| 100k+ users | May need to shard by user. Consider extracting Bank Sync to separate service (3rd party rate limits). |

### First Bottlenecks (In Order)

1. **Database reads for dashboards** - Add caching, materialized views
2. **Plaid rate limits** - Queue and batch sync requests
3. **Report generation** - Background jobs, pre-computed summaries
4. **Transaction write throughput** - Unlikely bottleneck for PFM scale

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Anemic Domain Model

**What people do:** Put all logic in services, make entities just data holders.
```typescript
// BAD: Anemic
class Account {
  id: string;
  balance: number;  // Just data
}

class AccountService {
  withdraw(account: Account, amount: number) {
    if (account.balance < amount) throw new Error();
    account.balance -= amount;
  }
}
```

**Why it's wrong:** Business rules scattered across services, hard to test, easy to bypass invariants.

**Do this instead:**
```typescript
// GOOD: Rich domain model
class Account extends AggregateRoot<AccountId> {
  private balance: Money;

  withdraw(amount: Money): void {
    if (!this.canWithdraw(amount)) {
      throw new InsufficientFundsError(this.id, amount);
    }
    this.balance = this.balance.subtract(amount);
    this.addDomainEvent(new FundsWithdrawn(this.id, amount));
  }

  canWithdraw(amount: Money): boolean {
    return this.balance.isGreaterThanOrEqual(amount);
  }
}
```

### Anti-Pattern 2: Treating Transfers as Two Transactions

**What people do:** Create separate withdrawal and deposit transactions.
```typescript
// BAD: Two transactions
await createTransaction({ accountId: from, amount: -100, type: 'withdrawal' });
await createTransaction({ accountId: to, amount: 100, type: 'deposit' });
```

**Why it's wrong:** Can get out of sync, no audit trail of the actual transfer, harder to query.

**Do this instead:** Use double-entry model where transfer is one transaction with two entries.
```typescript
// GOOD: Single transaction with entries
const transfer = Transaction.createTransfer(fromAccount, toAccount, amount);
// Contains: [Entry(from, -100), Entry(to, +100)]
```

### Anti-Pattern 3: Storing Money as Floats

**What people do:** `balance: 123.45` as a float.

**Why it's wrong:** Floating-point precision errors. `0.1 + 0.2 !== 0.3` in JavaScript.

**Do this instead:** Store as integer cents, use Money value object.
```typescript
balance_cents: 12345  // in database
Money.fromCents(12345, Currency.USD)  // in domain
```

### Anti-Pattern 4: Domain Objects Knowing About Persistence

**What people do:** Domain entities with decorators, ORMs in domain layer.
```typescript
// BAD: Domain coupled to ORM
@Entity()
class Account {
  @PrimaryColumn()
  id: string;

  @Column()
  balance: number;
}
```

**Why it's wrong:** Domain can't be tested without database, persistence concerns leak into business logic.

**Do this instead:** Pure domain objects, mappers in infrastructure.
```typescript
// GOOD: Pure domain
class Account extends AggregateRoot<AccountId> {
  // No decorators, no ORM knowledge
}

// Infrastructure handles mapping
class AccountMapper {
  static toDomain(row: AccountRow): Account { ... }
  static toPersistence(account: Account): AccountRow { ... }
}
```

### Anti-Pattern 5: Plaid Access Tokens on Frontend

**What people do:** Store access_token in frontend state or local storage.

**Why it's wrong:** Security breach - access tokens grant read access to user's bank accounts.

**Do this instead:** Only link_token and public_token on frontend. Access tokens encrypted and stored in backend only.

---

## Integration Points

### External Services

| Service | Integration Pattern | Security Considerations |
|---------|---------------------|------------------------|
| Plaid | REST API via SDK, Webhooks | Access tokens encrypted at rest, stored in DB. Never log tokens. Use environment-specific secrets. |
| Email (SendGrid/Resend) | Queue-based async | API keys in secrets manager. Rate limit outbound. |
| Redis | Direct connection | Use TLS in production. Separate instances per environment. |

### Plaid Webhook Handling

```typescript
// interfaces/http/webhooks/PlaidWebhookController.ts
export class PlaidWebhookController {
  constructor(
    private readonly syncUseCase: SyncTransactionsUseCase,
    private readonly plaidClient: PlaidApi
  ) {}

  async handleWebhook(req: Request, res: Response): Promise<void> {
    // 1. Verify webhook signature
    const isValid = await this.verifyWebhookSignature(req);
    if (!isValid) {
      res.status(401).send('Invalid signature');
      return;
    }

    // 2. Acknowledge immediately (Plaid expects fast response)
    res.status(200).send('OK');

    // 3. Process asynchronously
    const { webhook_type, webhook_code, item_id } = req.body;

    switch (webhook_type) {
      case 'TRANSACTIONS':
        if (webhook_code === 'SYNC_UPDATES_AVAILABLE') {
          // Queue sync job instead of processing inline
          await this.jobScheduler.enqueue('bank-sync', { itemId: item_id });
        }
        break;
      case 'ITEM':
        if (webhook_code === 'ERROR') {
          // Handle connection errors (e.g., credentials expired)
          await this.handleItemError(item_id, req.body.error);
        }
        break;
    }
  }
}
```

### Internal Module Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Accounts <-> Transactions | Direct method call (same process) | Share AccountId value object |
| Transactions -> Budgeting | Domain events (async) | TransactionRecorded triggers budget check |
| Bank Sync -> Transactions | Application service call | Reconciliation creates/updates Transactions |
| Any -> Reporting | Query service (read-only) | Reports have separate query models |

---

## Build Order Implications

Based on dependencies and complexity, recommended build order:

### Phase 1: Foundation
1. **Shared domain primitives** (Entity, ValueObject, AggregateRoot, DomainEvent)
2. **Money value object** (critical, used everywhere)
3. **Account aggregate** (simple, needed for transactions)
4. **Repository pattern** (establish data mapper approach early)

### Phase 2: Core Domain
5. **Transaction aggregate** (double-entry model)
6. **Transfer domain service** (validates cross-account operations)
7. **Category management** (simple CRUD, needed for transactions)

### Phase 3: Multi-Interface
8. **REST API** (primary interface)
9. **CLI** (useful for development/operations)
10. **Authentication integration** (secure the API)

### Phase 4: External Integration
11. **Plaid integration** (bank sync)
12. **Reconciliation service** (match imported transactions)
13. **Background jobs** (scheduled syncs, recurring transactions)

### Phase 5: Advanced Features
14. **Budgeting context** (depends on transactions working)
15. **Reporting queries** (read models, materialized views)
16. **AI interface** (builds on existing use cases)

### Phase 6: Operations
17. **Observability** (OpenTelemetry, metrics)
18. **Alerting** (budget notifications, sync failures)

---

## Sources

### DDD and Clean Architecture
- [ByteByteGo: Domain-Driven Design Demystified](https://blog.bytebytego.com/p/domain-driven-design-ddd-demystified) - HIGH confidence
- [DDD for Banking Application](https://medium.com/@shek.up/domain-driven-design-for-banking-application-d6279ecdaf2) - MEDIUM confidence
- [DDD in Fintech](https://trio.dev/domain-driven-design-in-fintech/) - MEDIUM confidence
- [Hexagonal vs Clean vs Onion 2026](https://dev.to/dev_tips/hexagonal-vs-clean-vs-onion-which-one-actually-survives-your-app-in-2026-273f) - MEDIUM confidence
- [GitHub: DDD Tutorial Personal Finance](https://github.com/intldds/ddd-domain-driven-design) - MEDIUM confidence

### Ports and Adapters / Hexagonal
- [Ports and Adapters with TypeScript](https://betterprogramming.pub/how-to-ports-and-adapter-with-typescript-32a50a0fc9eb) - MEDIUM confidence
- [GitHub: Hexagonal Example TypeScript](https://github.com/onicagroup/hexagonal-example) - MEDIUM confidence
- [Ports and Adapters Explained](https://rytheturtle.substack.com/p/ports-and-adapters-architecture-explained) - MEDIUM confidence

### Data Patterns
- [DTOs, Mappers, Repository in TypeScript DDD](https://khalilstemmler.com/articles/typescript-domain-driven-design/repository-dto-mapper/) - HIGH confidence
- [Martin Fowler: Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html) - HIGH confidence
- [Aggregate Design and Persistence](https://khalilstemmler.com/articles/typescript-domain-driven-design/aggregate-design-persistence/) - HIGH confidence

### Financial Domain
- [Double-Entry Accounting for Engineers](https://anvil.works/blog/double-entry-accounting-for-engineers) - HIGH confidence
- [Firefly III Architecture](https://docs.firefly-iii.org/explanation/more-information/architecture/) - MEDIUM confidence
- [Transaction Reconciliation](https://medium.com/actualbudget/how-transaction-reconciliation-works-8dc5749bbd21) - MEDIUM confidence

### CQRS and Event Sourcing
- [CQRS & Event Sourcing in Financial Services](https://iconsolutions.com/blog/cqrs-event-sourcing) - MEDIUM confidence
- [Event Sourcing in FinTech](https://lukasniessen.medium.com/this-is-a-detailed-breakdown-of-a-fintech-project-from-my-consulting-career-9ec61603709c) - MEDIUM confidence
- [Microsoft: CQRS Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs) - HIGH confidence

### Plaid Integration
- [Plaid API Documentation](https://plaid.com/docs/api/) - HIGH confidence
- [GitHub: Plaid Pattern Example](https://github.com/plaid/pattern) - HIGH confidence
- [Plaid Integration Guide 2026](https://www.fintegrationfs.com/post/how-to-integrate-plaid-with-your-fintech-app-a-complete-technical-guide-2026) - MEDIUM confidence

### Background Jobs
- [BullMQ Scheduled Tasks](https://betterstack.com/community/guides/scaling-nodejs/bullmq-scheduled-tasks/) - HIGH confidence
- [BullMQ Official](https://bullmq.io/) - HIGH confidence

### Observability
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/languages/js/getting-started/nodejs/) - HIGH confidence

---

*Architecture research for: Personal Finance Platform with DDD + Clean Architecture*
*Researched: 2026-01-29*
