import unittest
from datetime import datetime
from src.db.models.book_models import Book, BookContent, BookPrice
from colorama import Fore, Style  # Импортируем colorama

class TestBookModels(unittest.TestCase):
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

    def test_book_model(self):
        book = Book(
            id="1",
            title="Sample Book",
            url_img="http://example.com/img.jpg",
            category=["Fiction"],
            author=["Author"],
            year_of_create=datetime(2023, 1, 1),
            hidden=False
        )
        self.assertEqual(book.id, "1")
        self.assertEqual(book.title, "Sample Book")

    def test_book_content_model(self):
        content = BookContent(
            book_id="1",
            url_content="http://example.com/content.pdf"
        )
        self.assertEqual(content.book_id, "1")

    def test_book_price_model(self):
        price = BookPrice(
            book_id="1",
            price=100,
            price_rent_2week=10,
            price_rent_month=30,
            price_rent_3month=80
        )
        self.assertEqual(price.book_id, "1")

if __name__ == "__main__":
    unittest.main()