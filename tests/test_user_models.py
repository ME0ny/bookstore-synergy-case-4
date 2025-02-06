import unittest
from src.db.models.user_models import User, UserAuth, UserWallet
from colorama import Fore, Style  # Импортируем colorama

class TestUserModels(unittest.TestCase):
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

    def test_user_model(self):
        user = User(
            id="1",
            login="test@example.com",
            hashed_password="hashed_password",
            is_admin=False,
            yandex_id="123456",
            email="test@example.com"
        )
        self.assertEqual(user.id, "1")
        self.assertEqual(user.login, "test@example.com")
        self.assertEqual(user.hashed_password, "hashed_password")
        self.assertEqual(user.is_admin, False)
        self.assertEqual(user.yandex_id, "123456")
        self.assertEqual(user.email, "test@example.com")

    def test_user_model_optional_fields(self):
        # Проверяем, что поля hashed_password, yandex_id и email могут быть None
        user = User(
            id="2",
            login="user@example.com",
            is_admin=True
        )
        self.assertEqual(user.id, "2")
        self.assertEqual(user.login, "user@example.com")
        self.assertEqual(user.hashed_password, None)
        self.assertEqual(user.is_admin, True)
        self.assertEqual(user.yandex_id, None)
        self.assertEqual(user.email, None)

    def test_user_auth_model(self):
        auth = UserAuth(
            user_id="1",
            refresh_token="refresh_token_123"
        )
        self.assertEqual(auth.user_id, "1")
        self.assertEqual(auth.refresh_token, "refresh_token_123")

    def test_user_wallet_model(self):
        wallet = UserWallet(
            user_id="1",
            account=1000
        )
        self.assertEqual(wallet.user_id, "1")
        self.assertEqual(wallet.account, 1000)

if __name__ == "__main__":
    unittest.main()