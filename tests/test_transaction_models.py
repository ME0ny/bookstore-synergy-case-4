import unittest
from datetime import datetime
from src.db.models.transaction_models import UserTransaction, TransactionStatus
from colorama import Fore, Style  # Импортируем colorama

class TestTransactionModels(unittest.TestCase):
    def setUp(self):
        # Выводим имя текущего теста перед его выполнением
        print(f"{Fore.CYAN}Running test: {self._testMethodName}{Style.RESET_ALL}")

    def tearDown(self):
        # Выводим статус теста после его выполнения
        if hasattr(self, '_outcome'):  # Python 3.4+
            result = self._outcome.result
            if result.errors or result.failures:
                print(f"{Fore.RED}Test {self._testMethodName} FAILED{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}Test {self._testMethodName} PASSED{Style.RESET_ALL}")
        else:  # Python 3.3 and below
            if not self._resultForDoCleanups.wasSuccessful():
                print(f"{Fore.RED}Test {self._testMethodName} FAILED{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}Test {self._testMethodName} PASSED{Style.RESET_ALL}")

    def test_user_transaction_model(self):
        transaction = UserTransaction(
            user_id="1",
            book_id="1",
            date_buy=datetime(2023, 10, 1),
            price=100,
            status=TransactionStatus.BUY
        )
        self.assertEqual(transaction.user_id, "1")
        self.assertEqual(transaction.book_id, "1")

if __name__ == "__main__":
    unittest.main()