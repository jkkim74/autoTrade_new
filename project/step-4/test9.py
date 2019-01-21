"""
Présentation du module threading

http://docs.python.org/3.3/library/threading.html
"""
import time
import threading


class BankAccount():
    def __init__(self, initial_money=0, owner='Anonymous'):
        self.money = initial_money
        self.owner = owner
        # We will keep each write access to money in an history file
        # In order to understand what Python does with our money'
        self.history_file = open('tmp/%s' % (owner,), 'w')
        # self.history_file = open("tmp/test.txt",'w')
        self.money_lock = threading.Lock()

    def execute_deposit(self, amount, by='A customer'):
        self.history_file.write(
            'Customer %s is adding %s to bank account of %s containing %s\n' % (by, amount, self.owner, self.money))
        for ind in range(0, amount):
            self.money_lock.acquire()
            old_money = self.money
            self.history_file.write(
                'Customer %s is about to add 1 more to account for a new value of: %s\n' % (by, old_money + 1))
            self.money = old_money + 1
            self.money_lock.release()

        self.history_file.write('Account money after %s deposit: %s\n' % (by, self.money))

    def __del__(self):
        self.history_file.close()


my_account = BankAccount(1000, "WorldCompanyBigBoss")
my_account.execute_deposit(100, "First customer")
my_account.execute_deposit(200, "Second customer")

list_threads = []
for num_thread in range(1, 5):
    # t = threading.Thread(target=BankAccount.execute_deposit, args=(my_account, 5000,'Customer %d' % (num_thread,)))
    # This syntax will do the same job as the line just above
    t = threading.Thread(target=my_account.execute_deposit, args=(2, 'Customer %d' % (num_thread,)))
    print("thread name ==> ", t.getName())
    # list_threads.append(t)
    t.start()

print("All threads are started")
for t in list_threads:
    t.join()  # Wait until thread terminates its job
# [t.join() for t in list_threads]
print("All threads completed")


