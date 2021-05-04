import dateutil.parser


class ModelBase(object):
    """Super class for all models. Provides basic serialization."""

    __dump_attributes__ = []

    @classmethod
    def from_dict(cls, session, data_dict):
        """Creating an instance of the specific type from the data passed in
        the dictionary `data_dict`.
        """
        return cls(session, **data_dict)

    def __init__(self, session, **kwargs):
        self.session = session
        for key, value in kwargs.items():
            setattr(self, key, value)

    def dump(self):
        """Serialize the ModelBase object to a dictionary."""
        result = {}
        for attribute in self.__dump_attributes__:
            value = getattr(self, attribute)
            if value is not None:
                result[attribute] = value
        return result


class User(ModelBase):
    """Object representing an user.
    https://docs.finx.finleap.cloud/stable/#operation/getUser

    Attributes:
        id: internal figo user id
        full_name: full name
        email: email address
        language: two letter code for preferred language
        created_at: created datetime
    """

    # TODO: "email" and "password" can be also modified - should we add them
    #  here?
    __dump_attributes__ = ["full_name", "language"]

    id = None
    full_name = None
    email = None
    language = None
    created_at = None

    def __init__(self, session, **kwargs):
        super().__init__(session, **kwargs)

        if self.created_at:
            self.created_at = dateutil.parser.parse(self.created_at)

    def __str__(self):
        return f"User: {self.full_name} ({self.id}, {self.email})"


class LoginSettings(ModelBase):
    """Object representing login settings for a banking service.

    Attributes:
        bank_name: human readable bank of the bank
        supported: boolean, if set bank is supported
        icon: JSON list with icons (different resolutions)
        credentials: list of credentials needed to connect to the bank
        auth_type: kind of authentication used by the bank
        advice: any additional advice useful to locate the required credentials
    """

    __dump_attributes__ = [
        "id",
        "name",
        "icon",
        "supported",
        "country",
        "language",
        "bic",
        "access_methods",
        "bank_code",
    ]

    id = None
    name = None
    icon = None
    supported = None
    country = None
    language = None
    bic = None
    access_methods = None
    bank_code = None

    def __str__(self, *args, **kwargs):
        return f"LoginSettings: {self.name}"


class Account(ModelBase):
    """Object representing one bank account of the user, independent of the
    exact account type.

    Attributes:
        account_id: internal figo connect account id
        account_number: account number
        bank_code: bank code (BLZ)
        iban: iban code
        bic: bic code
        access_id: finX ID of the provider access
        bank_name: name of bank or financial provider.
        icon: JSON list with bank icons (different resolutions)
        currency: three character currency code
        balance: account balance
        type: account type, one of (Giro account, Savings account,
            Credit card, Loan account, PayPal, Cash book, Unknown)
        name: account name
        owner: account owner
        auto_sync: boolean value that indicates whether the account is
            automatically synchronized
        save_pin: indicates if the provider credentials are saved for this
            account (Default: false).
        supported_payments: mapping of payment types to payment parameters
            supported by this account.
        is_jointly_managed: indicates that the account has been opened by two
            or more individuals or entities.
        status: synchronization status object
    """

    account_id = None
    account_number = None
    bank_code = None
    iban = None
    bic = None
    access_id = None
    bank_name = None
    icon = None
    currency = None
    balance = None
    type = None
    name = None
    owner = None
    auto_sync = None
    save_pin = None
    supported_payments = None
    is_jointly_managed = None
    status = None

    @property
    def payments(self):
        """An array of `Payment` objects, one for each transaction on the
        account.
        """
        return self.session.get_payments(self.account_id)

    def get_payment(self, payment_id):
        """Retrieve a specific payment.

        Args:
            payment_id: id of the payment to be retrieved

        Returns:
            A Payment object representing the payment to be retrieved
        """
        return self.session.get_payments(self.account_id, payment_id)

    @property
    def transactions(self):
        """An array of `Transaction` objects, one for each transaction on the
        account.
        """
        return self.session.get_transactions(self.account_id)

    def get_transactions(
        self, since=None, count=1000, offset=0, include_pending=False
    ):
        """Get an array of `Transaction` objects, one for each transaction of
        the user.

        Args:
            since: This parameter can either be a transaction ID or a date.
            count: Limit the number of returned transactions
            offset: Offset into the result set to determine the first
                transaction returned (useful in combination with count)
            include_pending: boolean, indicates whether pending transactions
                should be included in the response; pending transactions are
                always included as a complete set, regardless of the `since`
                parameter.

        Returns:
            A list of Transaction objects
        """
        return self.session.get_transactions(
            self.account_id, since, count, offset, include_pending
        )

    def get_transaction(self, transaction_id):
        """Retrieve a specific transaction.

        Args:
            transaction_id: id of the transaction to be retrieved

        Returns:
            A Transaction object representing the transaction to be retrieved
        """
        return self.session.get_transaction(self.account_id, transaction_id)

    @property
    def securities(self):
        """An array of `Securities` objects, one for each security on the
        account.
        """
        return self.session.get_securities(self.account_id)

    def get_securities(self, since=None, count=1000, offset=0, accounts=None):
        """Get an array of Security objects, one for each security of the user.

        Args:
            account_id: ID of the account for which to list the securities
            since: This parameter can either be a transaction ID or a date.
            count: Limit the number of returned transactions
            offset: Offset into the result set to determine the first security
                returned (useful in combination with count)
            accounts: list of accounts. If retrieving the securities for all
                accounts, filter the securities to be only from these accounts.

        Returns:
            A list of Security objects
        """
        return self.session.get_securities(
            self.account_id, since, count, offset, accounts
        )

    def get_security(self, security_id):
        """Retrieve a specific security.

        Args:
             account_id: id of the account on which the security belongs
             security_id: id of the security to be retrieved

        Returns:
            A Security object representing the transaction to be retrieved
        """
        return self.session.get_security(self.account_id, security_id)

    def __str__(self):
        return (
            f"Account: {self.name} ({self.account_number} at {self.bank_name})"
        )

    def __init__(self, session, **kwargs):
        super(Account, self).__init__(session, **kwargs)
        if self.status:
            self.status = SynchronizationStatus.from_dict(
                self.session, self.status
            )
        if self.balance:
            self.balance = AccountBalance.from_dict(self.session, self.balance)


class AccountBalance(ModelBase):
    """Object representing the balance of a certain bank account of the user.

    Attributes:
        balance: acccount balance or None if the balance is not yet known
        balance_date: bank server timestamp of balance or None if the balance
            is not yet known.
        credit_line: credit line
        monthly_spending_limit: user-defined spending limit
        status: synchronization status object
    """

    balance = None
    balance_date = None
    status = None

    def __str__(self):
        return f"Balance: {self.balance} at {self.balance_date}"

    def __init__(self, session, **kwargs):
        super(AccountBalance, self).__init__(session, **kwargs)
        if self.status:
            self.status = SynchronizationStatus.from_dict(
                self.session, self.status
            )

        if self.balance_date:
            self.balance_date = dateutil.parser.parse(self.balance_date)


class Payment(ModelBase):
    """Object representing a Payment.

    When creating a new Payment for submitment to the Figo API all necessary
    fields have to be set on the Payment object.

    Attributes:
        payment_id: internal figo payment id
        account_id: internal figo account id
        type: payment type, one of (Transfer, Direct Debit, SEPA transfer,
            SEPA direct debit)
        name: name of creditor or debtor
        account_number: account number of creditor or debtor
        bank_code: bank code of creditor or debtor
        bank_code: bank name of creditor or debtor
        amount: order amount
        purpose: purpose text
        bank_icon: icon of creditor or debtor bank
        bank_additional_icons: dictionary that maps resolutions to icon URLs
        amount: order amount
        currency: three character currency code
        purpose: purpose text
        submission_timestamp: submission timestamp
        creation_timestamp: internal creation timestamp
        modification_timestamp: internal creation timestamp
        traditional_id: transaction id, only set if payment has been matched
            to a transaction
    """

    __dump_attributes__ = [
        "type",
        "name",
        "account_number",
        "bank_code",
        "amount",
        "currency",
        "purpose",
    ]

    payment_id = None
    account_id = None
    type = None
    name = None
    account_number = None
    bank_code = None
    bank_name = None
    bank_icon = None
    bank_additional_icons = None
    amount = None
    currency = None
    purpose = None
    submission_timestamp = None
    creation_timestamp = None
    modification_timestamp = None
    transaction_id = None

    def __init__(self, session, **kwargs):
        super(Payment, self).__init__(session, **kwargs)

        if self.submission_timestamp:
            self.submission_timestamp = dateutil.parser.parse(
                self.submission_timestamp
            )

        if self.creation_timestamp:
            self.creation_timestamp = dateutil.parser.parse(
                self.creation_timestamp
            )

        if self.modification_timestamp:
            self.modification_timestamp = dateutil.parser.parse(
                self.modification_timestamp
            )

    def __str__(self):
        return (
            f"Payment: {self.name} ({self.account_number} at {self.bank_name})"
        )


class StandingOrder(ModelBase):
    """Object representing one standing order on a certain bank account of the
    user.

    Attributes:
        standing_order_id: internal figo stanging order id
        account_id: internal figo account id
        iban: iban of creditor or debtor
        amount: order amount
        currency: three character currency code
        cents:
        name: name of originator or recipient
        purpose: purpose text
        execution_day: number of days of execution of the standing order
        first_execution_date: starting day of execution
        last_execution_date: finishing day of the execution
        interval:
        created_at: internal creation timestamp
        modified_at: internal creation timestamp
    """

    __dump_attributes__ = []

    standing_order_id = None
    account_id = None
    iban = None
    amount = None
    currency = None
    cents = None
    name = None
    purpose = None
    execution_day = None
    first_execution_date = None
    last_execution_date = None
    interval = None
    created_at = None
    modified_at = None

    def __init__(self, session, **kwargs):
        super(StandingOrder, self).__init__(session, **kwargs)

        if self.created_at:
            self.created_at = dateutil.parser.parse(self.created_at)

        if self.modified_at:
            self.modified_at = dateutil.parser.parse(self.modified_at)

        if self.first_execution_date:
            self.first_execution_date = dateutil.parser.parse(
                self.first_execution_date
            )

        if self.last_execution_date:
            self.last_execution_date = dateutil.parser.parse(
                self.last_execution_date
            )

    def __str__(self):
        return f"Standing Order: {self.standing_order_id}"


class Transaction(ModelBase):
    """Object representing one bank transaction on a certain bank account of
    the user.

    Attributes:
        account_id:  internal figo account id
        transaction_id: internal figo transaction id
        amount: transaction amount
        currency: three-character currency code
        account_number: account number of originator or recipient
        bank_code: bank code of originator or recipient
        iban: iban
        bic: bic
        bank_name: bank name of originator or recipient
        booked: boolean, indicates whether transaction is booked or pending
        booked_at: the date on which the transaction was booked
        settled_at: the date on which the transaction was settled
        booking_key: booking key
        booking_text: booking text
        categories: list of categories assigned to this transaction, ordered
            from general to specific
        contract_id: ID of the contract
        custom_category: Custom category matching the standard category.
            This attribute is only set if a custom category grouping has been
            defined
        creditor_id: FinTS: SEPA creditor identifier (for SEPA direct debits)
        end_to_end_reference: end to end reference
        mandate_reference: mandate reference
        name: name of originator or recipient
        prima_nota_number: prima nota number
        purpose: purpose text
        sepa_purpose_code: SEPA purpose code
        sepa_remittance_info: SEPA remittance info
        transaction_code: Transaction type as DTA Tx Key code.
        payment_partner: payment partner with name and ID
        type: transaction type, one of (Transfer, Standing order, Direct debit,
            Salary or rent, GeldKarte, Charges or interest)
        additional_info: provides more info about the transaction if available
        created_at: create date
        modified_at: modification date
    """

    __dump_attributes__ = [
        "account_id",
        "transaction_id",
        "amount",
        "currency",
        "account_number",
        "bank_code",
        "iban",
        "bic",
        "bank_name",
        "booked",
        "booked_at",
        "settled_at",
        "booking_key",
        "booking_text",
        "categories",
        "contract_id",
        "custom_category",
        "creditor_id",
        "end_to_end_reference",
        "mandate_reference",
        "name",
        "prima_nota_number",
        "purpose",
        "sepa_purpose_code",
        "sepa_remittance_info",
        "transaction_code",
        "payment_partner",
        "type",
        "additional_info",
        "created_at",
        "modified_at",
    ]

    account_id = None
    transaction_id = None
    amount = None
    currency = None
    account_number = None
    bank_code = None
    iban = None
    bic = None
    bank_name = None
    booked = None
    booked_at = None
    settled_at = None
    booking_key = None
    booking_text = None
    categories = None
    contract_id = None
    custom_category = None
    creditor_id = None
    end_to_end_reference = None
    mandate_reference = None
    name = None
    prima_nota_number = None
    purpose = None
    sepa_purpose_code = None
    sepa_remittance_info = None
    transaction_code = None
    payment_partner = None
    type = None
    additional_info = None
    created_at = None
    modified_at = None

    def __init__(self, session, **kwargs):
        super(Transaction, self).__init__(session, **kwargs)

        if self.created_at:
            self.created_at = dateutil.parser.parse(self.created_at)

        if self.modified_at:
            self.modified_at = dateutil.parser.parse(self.modified_at)

        if self.booked_at:
            self.booked_at = dateutil.parser.parse(self.booked_at)

        if self.settled_at:
            self.settled_at = dateutil.parser.parse(self.settled_at)

        if self.categories:
            self.categories = [
                Category.from_dict(session, c) for c in self.categories
            ]

        if self.custom_category:
            self.custom_category = CustomCategory.from_dict(
                session, self.custom_category
            )

        if self.payment_partner:
            self.payment_partner = PaymentPartner.from_dict(
                session, self.payment_partner
            )

    def __str__(self):
        return (
            f"Transaction: {self.amount} {self.currency} to {self.name} at "
            f"{self.settled_at}"
        )


class Category(ModelBase):
    """Object representing a category for a transaction

    Attributes:
        id: ID of the finX standard category.
        parent_id: ID of the parent category.
        name: category name
    """

    __dump_attributes__ = ["id", "parent_id", "name"]

    id = None
    parent_id = None
    name = None

    def __str__(self):
        return f"Category: {self.name}"


class CustomCategory(ModelBase):
    """Object representing a custom category for a transaction

    Attributes:
        id: ID of the custom category grouping
        name: category name
    """

    __dump_attributes__ = ["id", "name"]

    id = None
    name = None

    def __str__(self):
        return f"CustomCategory: {self.name}"


class PaymentPartner(ModelBase):
    """Object representing a payment partner for a transaction

    Attributes:
        id: payment partner ID
        name: name of payment partner
    """

    __dump_attributes__ = ["id", "name"]

    id = None
    name = None

    def __str__(self):
        return f"PaymentPartner: {self.name}"


class Notification(ModelBase):
    """Object representing a configured notification, e.g a webhook or email
    hook.

    Attributes:
        notification_id: internal figo notification ID from the notification
            registration response
        observe_key: notification key, see
            http://developer.figo.me/#notification_keys
        notify_uri: notification messages will be sent to this URL
        state: state similiar to sync and login process. It will passed as
            POST data for webhooks
    """

    __dump_attributes__ = ["observe_key", "notify_uri", "state"]

    notification_id = None
    observe_key = None
    notify_uri = None
    state = None

    def __str__(self):
        return f"Notification: {self.observe_key} triggering {self.notify_uri}"


class SynchronizationStatus(ModelBase):
    """Object representing the synchronization status of the figo servers with
    banks, payment providers or financial service providers.

    Attributes:
        synced_at: timestamp of last synchronization
        succeeded_at: timestamp of last successful synchronization
        message: human-readable error message
    """

    __dump_attributes__ = []

    synced_at = None
    succeeded_at = None
    message = None

    def __init__(self, session, **kwargs):
        super(SynchronizationStatus, self).__init__(session, **kwargs)
        if self.synced_at:
            self.synced_at = dateutil.parser.parse(self.synced_at)

        if self.succeeded_at:
            self.succeeded_at = dateutil.parser.parse(self.succeeded_at)

    def __str__(self):
        return f"Synchronization Status: {self.message}"


class Sync(ModelBase):
    """Object representing a syncronisation for account creation.

    Attributes:
        id: internal figo syncronisation id
        status: Current processing state of the item.
        state: The state that was being provided in the request when creating
            the synchronization.
        challenge: AuthMethodSelectChallenge (object) or EmbeddedChallenge
            (object) or RedirectChallenge (object) or DecoupledChallenge
            (object) (Challenge).
        error: Error detailing why the background operation failed.
        created_at: Time at which the sync was created
        started_at: Time at which the sync started
        ended_at: Time at which the sync ended
    """

    __dump_attributes__ = [
        "id",
        "status",
        "state",
        "challenge",
        "error",
        "created_at",
        "started_at",
        "ended_at",
    ]

    id = None
    status = None
    state = None
    challenge = None
    error = None
    created_at = None
    started_at = None
    ended_at = None

    def __init__(self, session, **kwargs):
        super(Sync, self).__init__(session, **kwargs)
        if self.created_at:
            self.created_at = dateutil.parser.parse(self.created_at)

        if self.started_at:
            self.started_at = dateutil.parser.parse(self.started_at)

        if self.ended_at:
            self.ended_at = dateutil.parser.parse(self.ended_at)

        if self.challenge:
            self.challenge = Challenge.from_dict(self.session, self.challenge)

    def __str__(self):
        return f"Sync: {self.id} Status: {self.status}"

    def dump(self):
        dumped_value = super(Sync, self).dump()
        if self.challenge:
            dumped_value.update({"challenge": self.challenge.dump()})

        return dumped_value


class WebhookNotification(ModelBase):
    """Object representing a WebhookNotification.

    Attributes:
        notification_id: internal figo notification ID from the notification
            registration response
        observe_key: notification key
        state: the state parameter from the notification registration request
        data: object or list with the data (AccountBalance or Transaction)
    """

    __dump_attributes__ = []

    notification_id = None
    observe_key = None
    state = None
    data = None

    def __str__(self):
        return f"WebhookNotification: {self.notification_id}"


class Credential(ModelBase):
    """Object representing a login credential field for a banking service.

    Attributes:
        label: label for text input field
        masked: boolean, if set the text input field is used for password
            entry and should be masked
        optional: boolean, if set the field is optional and may be an empty
            string
    """

    __dump_attributes__ = ["label", "masked", "optional"]

    label = None
    masked = None
    optional = None

    def __str__(self, *args, **kwargs):
        return f"Credential: {self.label}"


class Challenge(ModelBase):
    """Object representing a challenge.

    Attributes:
        title: challenge title
        label: response label
        format: challenge data format, one of (Text, HTML, HHD, Matrix)
        data: challenge data

    """

    __dump_attributes__ = [
        "id",
        "title",
        "label",
        "format",
        "data",
        "type",
        "location",
        "created_at",
    ]

    id = None
    title = None
    label = None
    format = None
    data = None
    type = None
    location = None
    created_at = None

    def __str__(self, *args, **kwargs):
        return f"Challenge: {self.title}"


class Security(ModelBase):
    """Object representing one bank security on a certain bank account of the
    user.

    Attributes:
        account_id: internal figo connect account id
        security_id: internal figo connect security id
        amount: monetary value in account currency
        amount_original_currency: monetary value in trading currency
        created_at: ?
        currency: three character currency code
        exchange_rate: exchange rate between trading and account currency
        isin: international securities identification number
        market: ?
        modified_at: ?
        name: name of the security
        price: trading price
        price_currency: currency of current price
        purchase_price: purchase price
        purchase_price_currency: currency of purchase price
        modified_at: ?
        wkn: wertpapierkennnummer (domestic security identification number)
        quantity: number of securities or value




        visited: boolean that indicates whether the security has been marked
            as visited by the user
        trade_timestamp: trade timestamp
        creation_timestamp: internal creation timestamp
        modification_timestamp: internal modification timestamp

    """

    __dump_attributes__ = []

    security_id = None
    account_id = None
    name = None
    isin = None
    wkn = None
    currency = None
    amount = None
    quantity = None
    amount_original_currency = None
    exchange_rate = None
    price = None
    price_currency = None
    purchase_price = None
    purchase_price_currency = None
    visited = None
    trade_timestamp = None
    creation_timestamp = None
    modification_timestamp = None

    def __init__(self, session, **kwargs):
        super(Security, self).__init__(session, **kwargs)

        if self.trade_timestamp:
            self.trade_timestamp = dateutil.parser.parse(self.trade_timestamp)

        if self.creation_timestamp:
            self.creation_timestamp = dateutil.parser.parse(
                self.creation_timestamp
            )

        if self.modification_timestamp:
            self.modification_timestamp = dateutil.parser.parse(
                self.modification_timestamp
            )

    def __str__(self):
        return (
            f"Security: {self.amount} {self.currency} to {self.name} at "
            f"{self.trade_timestamp}"
        )
