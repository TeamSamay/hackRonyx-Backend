import os
import pandas as pd
import openpyxl
import fitz  # PyMuPDF

DATASETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data"))
DOCUMENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data", "documents"))
os.makedirs(DATASETS_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

def generate_csv_and_excel():
    print("Generating CSV datasets...")
    # Customers CSV
    customers = [
        {"customer_id": f"CUST-{1000+i}", "name": name, "age": 25 + i * 2, "city": city, "state": state, "email": f"{name.lower().replace(' ', '.')}@example.com", "phone": f"+91 98765 432{i:02d}", "customer_since": "2022-04-12", "account_status": "ACTIVE", "kyc_status": "VERIFIED"}
        for i, (name, city, state) in enumerate([
            ("Rahul Sharma", "Mumbai", "Maharashtra"),
            ("Priya Patel", "Ahmedabad", "Gujarat"),
            ("Amit Verma", "Delhi", "Delhi"),
            ("Neha Gupta", "Bangalore", "Karnataka"),
            ("Suresh Kumar", "Chennai", "Tamil Nadu"),
            ("Vikram Singh", "Jaipur", "Rajasthan")
        ])
    ]
    df_cust = pd.DataFrame(customers)
    df_cust.to_csv(os.path.join(DATASETS_DIR, "customers.csv"), index=False)

    # Accounts CSV
    accounts = [
        {"account_id": "ACC-92831", "customer_id": "CUST-1000", "account_type": "SAVINGS", "opened_date": "2022-04-12", "balance": 482000.0, "status": "ACTIVE", "branch": "Mumbai Main"},
        {"account_id": "ACC-1002", "customer_id": "CUST-1001", "account_type": "CURRENT", "opened_date": "2023-01-15", "balance": 1250000.0, "status": "ACTIVE", "branch": "Ahmedabad SG Highway"},
        {"account_id": "ACC-1003", "customer_id": "CUST-1002", "account_type": "SAVINGS", "opened_date": "2021-09-01", "balance": 85000.0, "status": "ACTIVE", "branch": "Delhi CP"}
    ]
    df_acc = pd.DataFrame(accounts)
    df_acc.to_csv(os.path.join(DATASETS_DIR, "accounts.csv"), index=False)

    # Transactions CSV
    transactions = [
        {"transaction_id": "TX-92831", "account_id": "ACC-92831", "timestamp": "2026-09-26 10:42", "amount": 85000.0, "currency": "INR", "merchant": "ABC Electronics", "merchant_category": "Electronics", "location": "Mumbai", "payment_method": "UPI", "device_id": "DEV-1001", "ip_address": "103.21.244.2", "status": "SUCCESS"},
        {"transaction_id": "TX-1002", "account_id": "ACC-92831", "timestamp": "2026-09-25 18:30", "amount": 1200.0, "currency": "INR", "merchant": "Starbucks Coffee", "merchant_category": "Dining", "location": "Mumbai", "payment_method": "DEBIT_CARD", "device_id": "DEV-1001", "ip_address": "103.21.244.2", "status": "SUCCESS"},
        {"transaction_id": "TX-1003", "account_id": "ACC-92831", "timestamp": "2026-09-24 14:15", "amount": 4500.0, "currency": "INR", "merchant": "Supermarket Retail", "merchant_category": "Groceries", "location": "Mumbai", "payment_method": "UPI", "device_id": "DEV-1001", "ip_address": "103.21.244.2", "status": "SUCCESS"}
    ]
    df_tx = pd.DataFrame(transactions)
    df_tx.to_csv(os.path.join(DATASETS_DIR, "transactions.csv"), index=False)

    # Devices CSV
    devices = [
        {"device_id": "DEV-1001", "customer_id": "CUST-1000", "device_type": "iPhone 14", "registered_city": "Mumbai", "last_seen_city": "Delhi", "last_seen_time": "2026-09-26 10:43", "device_status": "ACTIVE"},
        {"device_id": "DEV-1002", "customer_id": "CUST-1001", "device_type": "Samsung S23", "registered_city": "Ahmedabad", "last_seen_city": "Ahmedabad", "last_seen_time": "2026-09-25 20:00", "device_status": "ACTIVE"}
    ]
    df_dev = pd.DataFrame(devices)
    df_dev.to_csv(os.path.join(DATASETS_DIR, "devices.csv"), index=False)

    print("Generating Excel workbook transactions.xlsx...")
    wb = openpyxl.Workbook()
    # Sheet 1: Transactions
    ws1 = wb.active
    ws1.title = "Transactions"
    ws1.append(["Transaction ID", "Account ID", "Timestamp", "Amount", "Merchant", "Location", "Device ID", "Status"])
    for t in transactions:
        ws1.append([t["transaction_id"], t["account_id"], t["timestamp"], t["amount"], t["merchant"], t["location"], t["device_id"], t["status"]])

    # Sheet 2: Customers
    ws2 = wb.create_sheet(title="Customers")
    ws2.append(["Customer ID", "Name", "City", "KYC Status", "Account Status"])
    for c in customers:
        ws2.append([c["customer_id"], c["name"], c["city"], c["kyc_status"], c["account_status"]])

    # Sheet 3: Devices
    ws3 = wb.create_sheet(title="Devices")
    ws3.append(["Device ID", "Customer ID", "Registered City", "Last Seen City", "Last Seen Time"])
    for d in devices:
        ws3.append([d["device_id"], d["customer_id"], d["registered_city"], d["last_seen_city"], d["last_seen_time"]])

    wb.save(os.path.join(DATASETS_DIR, "transactions.xlsx"))
    print("Excel workbook saved!")

def create_pdf(filename: str, title: str, paragraphs: list):
    pdf_path = os.path.join(DOCUMENTS_DIR, filename)
    doc = fitz.open()
    page = doc.new_page()

    # Insert Title
    rect = fitz.Rect(50, 50, 550, 90)
    page.insert_textbox(rect, title, fontsize=18, color=(0.1, 0.2, 0.6), align=fitz.TEXT_ALIGN_LEFT)

    # Insert Paragraphs
    y = 100
    for p in paragraphs:
        rect = fitz.Rect(50, y, 550, y + 40)
        page.insert_textbox(rect, p, fontsize=11, color=(0.1, 0.1, 0.1), align=fitz.TEXT_ALIGN_LEFT)
        y += 45

    doc.save(pdf_path)
    doc.close()
    print(f"Generated PDF: {filename}")

def generate_sample_pdfs():
    print("Generating PDF documents...")
    # PDF 1: Customer KYC
    create_pdf("customer_1001_kyc.pdf", "ENTERPRISE KYC VERIFICATION RECORD", [
        "Customer Name: Rahul Sharma",
        "Customer ID: CUST-1001 | Document Type: Permanent Account Number (PAN)",
        "Registered Address: 402 Nariman Point, Marine Drive, Mumbai, Maharashtra 400021",
        "Verification Status: VERIFIED | Verification Date: 2026-01-10",
        "Issuing Authority: Income Tax Department, Govt of India | Status: ACTIVE"
    ])

    # PDF 2: Bank Statement
    create_pdf("account_92831_statement.pdf", "BANK ACCOUNT STATEMENT - ACC-92831", [
        "Account Holder: Rahul Sharma | Account Number: ACC-92831",
        "Branch: Nariman Point, Mumbai | Currency: INR",
        "Opening Balance: ₹4,50,000.00 | Closing Balance: ₹4,82,000.00",
        "Recent Transaction: 2026-09-26 10:42 AM - Transfer ₹85,000 to ABC Electronics (Mumbai)",
        "Velocity Baseline: Average monthly transfer ₹8,400 with 98% Mumbai location affinity."
    ])

    # PDF 3: Company Financial Statement
    create_pdf("abc_technologies_financial_statement.pdf", "ABC TECHNOLOGIES PRIVATE LIMITED - FINANCIAL STATEMENT", [
        "Company Name: ABC Technologies Private Limited",
        "Reporting Period: FY 2025-2026 | Currency: INR",
        "Gross Revenue: ₹12,45,00,000 | Net Operating Profit: ₹2,15,00,000",
        "Total Assets: ₹8,90,00,000 | Total Liabilities: ₹1,50,00,000",
        "Auditor Opinion: UNQUALIFIED CLEAN AUDIT | Registered Office: Pune, Maharashtra"
    ])

    # PDF 4: Company Registration
    create_pdf("abc_technologies_registration.pdf", "CERTIFICATE OF INCORPORATION & REGISTRATION", [
        "Company Name: ABC Technologies Private Limited",
        "Corporate Identity Number (CIN): U72900PN2020PTC192831",
        "Registered Address: Tech Park Tower 4, Hinjewadi, Pune, Maharashtra 411057",
        "Incorporation Date: 14th March 2020 | Registrar of Companies: ROC Pune",
        "Active Directors: Rahul Sharma, Priya Patel"
    ])

    # PDF 5: Tax GST Record
    create_pdf("abc_technologies_tax_record.pdf", "GOVERNMENT TAX & GST COMPLIANCE RECORD", [
        "Taxpayer Name: ABC Technologies Private Limited",
        "GSTIN / Tax ID: 27AAACA92831Z1Z5 | State: Maharashtra",
        "Declared Quarterly Revenue: ₹3,10,00,000 | GST Paid: ₹55,80,000",
        "Filing Status: UP_TO_DATE | Tax Clearance Certificate Issued: 2026-08-15"
    ])

if __name__ == "__main__":
    generate_csv_and_excel()
    generate_sample_pdfs()
    print("All synthetic enterprise files generated successfully!")
