"""Exo 2 - CloudGear Outdoor Rentals (implementation of the UML class diagram)."""
from abc import ABC, abstractmethod
from datetime import date


# ---------------- Equipment Items ----------------
class Equipment(ABC):
    def __init__(self, equip_id, name, daily_rate, stock):
        self.id = equip_id
        self.name = name
        self.daily_rate = daily_rate
        self.stock = stock

    def is_in_stock(self, quantity=1):
        return self.stock >= quantity


class Tent(Equipment):
    pass


class Kayak(Equipment):
    pass


# ---------------- Customers ----------------
class Customer(ABC):
    def __init__(self, customer_id, name):
        self.id = customer_id
        self.name = name
        self.bookings = []

    @abstractmethod
    def discount_rate(self):
        ...

    @abstractmethod
    def can_backorder(self):
        ...

    def create_booking(self, lines, days):
        booking = Booking(self, lines, days)
        self.bookings.append(booking)
        return booking


class VIPExplorer(Customer):
    def discount_rate(self):
        return 0.15            # 15% discount + priority supplier sourcing

    def can_backorder(self):
        return True


class StandardExplorer(Customer):
    def discount_rate(self):
        return 0.0

    def can_backorder(self):
        return False


class GuestVisitor:
    def __init__(self, name):
        self.name = name


class MembershipForm:
    def __init__(self, visitor):
        self.visitor = visitor


# ---------------- Bookings ----------------
class BookingLine:
    def __init__(self, equipment, quantity):
        self.equipment = equipment
        self.quantity = quantity
        self.backordered = False

    def subtotal(self, days):
        return self.equipment.daily_rate * self.quantity * days


class Booking:
    def __init__(self, customer, lines, days):
        self.customer = customer
        self.lines = lines       # Booking 1 *-- 1..* BookingLine (Composition)
        self.days = days
        self.date = date.today()
        self.status = "NEW"
        self.bill = None
        self.dispatch_note = None


class RentalBill:
    def __init__(self, booking, amount):
        self.booking = booking
        self.amount = amount
        self.settled = False


class DispatchNote:
    def __init__(self, booking, ready_lines):
        self.booking = booking
        self.ready_lines = ready_lines


# ---------------- Payments ----------------
class RentalPayment(ABC):
    def __init__(self, bill):
        self.bill = bill

    @abstractmethod
    def execute(self):
        ...


class CashRentalPayment(RentalPayment):
    def execute(self):
        self.bill.settled = True
        return "cash"


class CardRentalPayment(RentalPayment):
    def __init__(self, bill, card_last4):
        super().__init__(bill)
        self.card_last4 = card_last4

    def execute(self):
        self.bill.settled = True
        return f"card *{self.card_last4}"


class VoucherPayment(RentalPayment):
    def __init__(self, bill, voucher_code):
        super().__init__(bill)
        self.voucher_code = voucher_code

    def execute(self):
        self.bill.settled = True
        return f"voucher {self.voucher_code}"


# ---------------- Staff ----------------
class BookingDeskAgent:
    def __init__(self):
        self.daily_log = []              # all processed/rejected bookings saved daily

    def handle_request(self, person, lines=None, days=1):
        """Only registered explorers can book. Guests receive a membership form."""
        if isinstance(person, GuestVisitor):
            return MembershipForm(person)
        return self.process_booking(person.create_booking(lines, days))

    def process_booking(self, booking):
        customer = booking.customer
        ready_items = []
        for line in booking.lines:
            if line.equipment.is_in_stock(line.quantity):
                ready_items.append(line)
            elif customer.can_backorder():           # VIP privilege only
                line.backordered = True              # sourced from partner warehouse
            else:
                booking.status = "REJECTED"
                self.daily_log.append(booking)
                return booking

        raw_total = sum(l.subtotal(booking.days) for l in booking.lines)
        final_amount = round(raw_total * (1 - customer.discount_rate()), 2)
        booking.bill = RentalBill(booking, final_amount)
        booking.dispatch_note = DispatchNote(booking, ready_items)

        for line in ready_items:
            line.equipment.stock -= line.quantity

        booking.status = "CONFIRMED"
        self.daily_log.append(booking)
        return booking


class BillingCashier:
    def settle_bill(self, payment):
        return payment.execute()


if __name__ == "__main__":
    # Scenario: VIP Explorer books 2 items for 2 days (1 out of stock), pays by voucher.
    tent = Tent(101, "Alpine 4-Season Tent", 40.0, stock=3)
    kayak = Kayak(102, "Sea Touring Kayak", 60.0, stock=0)     # out of stock
    vip = VIPExplorer("VIP-01", "Camille")
    agent = BookingDeskAgent()
    cashier = BillingCashier()

    booking = agent.handle_request(vip, [BookingLine(tent, 1), BookingLine(kayak, 1)], days=2)
    assert booking.status == "CONFIRMED"
    assert booking.lines[1].backordered and not booking.lines[0].backordered
    assert booking.bill.amount == 170.0                        # (40*2 + 60*2) * 0.85
    assert len(booking.dispatch_note.ready_lines) == 1         # only the in-stock tent dispatches
    cashier.settle_bill(VoucherPayment(booking.bill, "GEAR-2026"))
    assert booking.bill.settled

    # Standard Explorer cannot backorder out-of-stock equipment
    standard = StandardExplorer("STD-09", "Hugo")
    rejected = agent.handle_request(standard, [BookingLine(kayak, 1)], days=1)
    assert rejected.status == "REJECTED"

    # Guest visitor receives a membership registration form
    assert isinstance(agent.handle_request(GuestVisitor("Chloe")), MembershipForm)
    assert len(agent.daily_log) == 2
    print("CloudGear Rentals: all checks passed.")