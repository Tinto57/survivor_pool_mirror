import csv
import io
from transactions.models import Transaction


def export_transactions() -> str:
    """Export the transactions in the DB in a clean csv file"""
    output = io.StringIO()
    fieldnames = [
        'id',
        'date_iso8601',
        'employee_id',
        'partner_id',
        'amount_cents',
        'status',
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()

    transactions = Transaction.objects.select_related(
        'employee', 'partner'
    ).order_by('id')

    for tx in transactions:
        date_str = tx.validated_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        amount_cents = int(round(tx.amount * 100))

        status = 'CANCELLED' if tx.is_cancelled else 'VALIDATED'

        writer.writerow({
            'id': tx.id,
            'date_iso8601': date_str,
            'employee_id': tx.employee_id,
            'partner_id': tx.partner_id,
            'amount_cents': amount_cents,
            'status': status,
        })

    return output.getvalue()
