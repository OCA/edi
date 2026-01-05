This addon extends the UBL/CII import process to handle archived partner bank
accounts correctly.

During invoice import, archived bank accounts are included in the lookup.
If a matching archived bank account is found, it is automatically reactivated
instead of creating a new one, thereby avoiding SQL constraint errors on
unique bank account numbers.

For safety reasons, when a bank account is reactivated through the import
process, the **"Send Money" option is automatically set to False**.
This ensures that the reactivated bank account can't be used for
outgoing payments without **manual validation** by an accountant or financial
responsible.
