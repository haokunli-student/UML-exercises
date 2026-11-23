"""Exo 1 - Smart Library Management System (implementation of the UML class diagram)."""
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class LoanStatus(Enum):
    REQUESTED = "requested"
    ACTIVE = "active"
    RETURNED = "returned"


# ---------------- Users (abstract superclass) ----------------
class User(ABC):
    def __init__(self, user_id, name, password):
        self._id = user_id
        self._name = name
        self._password = password
        self._logged_in = False

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    def login(self, password):
        self._logged_in = password == self._password
        return self._logged_in

    def logout(self):
        self._logged_in = False

    @abstractmethod
    def role(self):
        ...


class Reader(User):
    def __init__(self, user_id, name, password):
        super().__init__(user_id, name, password)
        self.loans = []             # 1 reader -> 0..* LoanRecord

    def role(self):
        return "reader"

    def request_book(self, book_title):
        loan = LoanRecord(len(self.loans) + 1, book_title, self)
        self.loans.append(loan)
        return loan

    def pay_fine(self, loan, payment):
        payment.process()
        loan.payment = payment
        return payment


class CatalogSpecialist(User):
    def __init__(self, user_id, name, password, section):
        super().__init__(user_id, name, password)
        self.section = section

    def role(self):
        return "catalog_specialist"

    def issue_receipt(self, loan, shelf_code):
        receipt = LoanReceipt(shelf_code, loan)
        loan.receipt = receipt
        loan.status = LoanStatus.ACTIVE
        return receipt


class Librarian(User):
    """Coordinator and administrator of the library platform."""

    def __init__(self, user_id, name, password):
        super().__init__(user_id, name, password)
        self.members = {}           # database of registered users (id -> user)
        self.fines_settled = []

    def role(self):
        return "librarian"

    # ---- administrator part ----
    def register_member(self, member_class, name, *extra):
        new_id = f"L{len(self.members) + 1:03d}"
        password = f"lib-{new_id}"          # issued by the librarian
        member = member_class(new_id, name, password, *extra)
        self.members[new_id] = member
        return member

    # ---- workflow part ----
    def verify_request(self, loan):
        loan.status = LoanStatus.ACTIVE
        return loan

    def assign_specialist(self, specialist, loan):
        loan.specialist = specialist
        return specialist.issue_receipt(loan, f"SHELF-{loan.id:02d}")

    def notify_reader(self, reader, receipt):
        return f"Pickup notice sent to {reader.name}: {receipt.shelf_code}"

    def record_fine_settlement(self, specialist, payment):
        self.fines_settled.append((specialist.name, payment.amount))
        return True


# ---------------- Core domain classes ----------------
class LoanRecord:
    def __init__(self, loan_id, book_title, reader):
        self.id = loan_id
        self.book_title = book_title
        self.reader = reader
        self.status = LoanStatus.REQUESTED
        self.created_at = datetime.now()
        self.specialist = None
        self.receipt = None         # 0..1
        self.payment = None


class LoanReceipt:
    def __init__(self, shelf_code, loan):
        self.shelf_code = shelf_code
        self.loan = loan
        self.issued_at = datetime.now()     # timestamp; kept in borrowing history


# ---------------- Fine Payment (Strategy via polymorphism) ----------------
class FinePayment(ABC):
    def __init__(self, amount):
        self.amount = amount
        self.paid = False
        self.date = datetime.now()

    @abstractmethod
    def process(self):
        ...


class CashFinePayment(FinePayment):
    def process(self):
        self.paid = True
        return f"Cash fine received: {self.amount}"


class CampusCardPayment(FinePayment):
    def __init__(self, amount, card_id):
        super().__init__(amount)
        self.card_id = card_id

    def process(self):
        self.paid = True
        return f"Campus card {self.card_id} debited: {self.amount}"


class OnlineTransferPayment(FinePayment):
    def __init__(self, amount, tx_ref):
        super().__init__(amount)
        self.tx_ref = tx_ref

    def process(self):
        self.paid = True
        return f"Online transfer {self.tx_ref} confirmed: {self.amount}"


if __name__ == "__main__":
    # Scenario: reader requests a book, receives a pickup receipt, settles a late fee.
    librarian = Librarian("LIB01", "Mme. Laurent", "admin123")
    reader = librarian.register_member(Reader, "Lucas")
    specialist = librarian.register_member(CatalogSpecialist, "M. Moreau", "Computer Science")

    loan = reader.request_book("Clean Architecture")
    assert loan.status is LoanStatus.REQUESTED

    librarian.verify_request(loan)
    assert loan.status is LoanStatus.ACTIVE

    receipt = librarian.assign_specialist(specialist, loan)
    assert receipt.shelf_code == "SHELF-01"
    print(librarian.notify_reader(reader, receipt))

    fine = CampusCardPayment(15.0, "STU-9088")
    reader.pay_fine(loan, fine)
    assert fine.paid
    librarian.record_fine_settlement(specialist, fine)
    assert librarian.fines_settled == [("M. Moreau", 15.0)]

    # Verify borrowing history retention
    history = [item.receipt for item in reader.loans if item.receipt]
    assert len(history) == 1
    print("Smart Library: all checks passed.")