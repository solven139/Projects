import MetaTrader5 as mt5
from mt5_config import login_number , path

result = mt5.initialize(path)
print('Connection result:', result)

if mt5.account_info().login == login_number:
    print('Login Number Correct')
else:
    print('Login Number Incorrect')
    exit()

account_data = mt5.account_info()
login = account_data.login
balance = account_data.balance
equity = account_data.equity

print('Login：', login)
print('Balance：', balance)
print('Equity：', equity)