import unittest
from datetime import datetime
from src.db.models.feed_models import FeedBook, FeedBookStatus, ReadBook
from src.db.models.book_models import Book, BookPrice
from colorama import Fore, Style  # Импортируем colorama

class TestFeedModels(unittest.TestCase):
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

    def test_feed_book_model(self):
        book = Book(
            id="1",
            title="Sample Book",
            url_img="http://example.com/img.jpg",
            category=["Fiction"],
            author=["Author"],
            year_of_create=datetime(2023, 1, 1),
            hidden=False
        )
        price = BookPrice(
            book_id="1",
            price=100,
            price_rent_2week=10,
            price_rent_month=30,
            price_rent_3month=80
        )
        feed_book = FeedBook(
            book=book,
            price=price,
            open_for_read=True,
            status=FeedBookStatus.BUY
        )
        self.assertEqual(feed_book.book.id, "1")
        self.assertEqual(feed_book.price.price, 100)

    def test_read_book_model(self):
        read_book = ReadBook(
            user_id="1",
            book_id="1",
            current_page=10
        )
        self.assertEqual(read_book.user_id, "1")
        self.assertEqual(read_book.book_id, "1")

if __name__ == "__main__":
    unittest.main()