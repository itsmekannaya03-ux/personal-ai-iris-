# Define a simple class for a Bank Account
class BankAccount:
    # Initialize the class with a balance and account number
    def __init__(self, account_number, initial_balance):
        self.account_number = account_number
        self.balance = initial_balance

    # Method to deposit money into the account
    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            return f"Deposited ${amount}. New balance: ${self.balance}"
        else:
            return "Invalid deposit amount"

    # Method to withdraw money from the account
    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            return f"Withdrew ${amount}. New balance: ${self.balance}"
        else:
            return "Invalid withdrawal amount"

    # Method to display the account details
    def display_details(self):
        return f"Account Number: {self.account_number}\nBalance: ${self.balance}"

# Create a new BankAccount object
account = BankAccount("123456789", 1000)

# Display the initial account details
print(account.display_details())

# Deposit $500 into the account
print(account.deposit(500))

# Withdraw $200 from the account
print(account.withdraw(200))

# Display the updated account details
print(account.display_details())