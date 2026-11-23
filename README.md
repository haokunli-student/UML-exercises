# UML-exercises

## Exo 1: Smart Library Management System

### Class Diagram (Tasks 1, 2, 3)
```mermaid
classDiagram
    class User {
        <<abstract>>
        #id: str
        #name: str
        #password: str
        +login(password) bool
        +logout()
    }
    class Reader {
        +requestBook(title)
        +payFine(loan, payment)
    }
    class CatalogSpecialist {
        -section: str
        +issueReceipt(loan, shelfCode)
    }
    class Librarian {
        +registerMember()
        +verifyRequest(loan)
        +assignSpecialist(specialist, loan)
        +notifyReader(reader, receipt)
        +recordFineSettlement(specialist, payment)
    }
    class LoanRecord {
        -id: int
        -bookTitle: str
        -createdAt: datetime
        -status: LoanStatus
    }
    class LoanReceipt {
        -shelfCode: str
        -issuedAt: datetime
    }
    class FinePayment {
        <<abstract>>
        -amount: float
        -date: datetime
        +process()
    }
    class CashFinePayment {
        +process()
    }
    class CampusCardPayment {
        -cardId: str
        +process()
    }
    class OnlineTransferPayment {
        -txRef: str
        +process()
    }
    class LoanStatus {
        <<enumeration>>
        REQUESTED
        ACTIVE
        RETURNED
    }
    User <|-- Reader
    User <|-- CatalogSpecialist
    User <|-- Librarian
    FinePayment <|-- CashFinePayment
    FinePayment <|-- CampusCardPayment
    FinePayment <|-- OnlineTransferPayment
    Reader "1" --> "0..*" LoanRecord : submits
    Librarian "1" --> "0..*" LoanRecord : verifies
    LoanRecord "0..*" --> "0..1" CatalogSpecialist : handled by
    LoanRecord "1" --> "0..1" LoanReceipt : generates
    Reader "1" --> "0..*" FinePayment : pays
    FinePayment "0..1" --> "1" LoanRecord : settles
    Librarian "1" --> "0..*" FinePayment : records settlement
