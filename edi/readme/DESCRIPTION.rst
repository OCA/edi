Base EDI backend.

Provides following models:

1. EDI Backend, to centralize configuration
2. EDI Backend Type, to classify EDI backends (eg: UBL, GS1, e-invoice, pick-yours)
3. EDI Exchange Type, to define file types of exchange
4. EDI Exchange Record, to define a record exchanged between systems

Also define a mixin to be inherited by records that will generate EDIs
