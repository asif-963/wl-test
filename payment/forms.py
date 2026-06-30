from django import forms
import json
from pathlib import Path
from django.conf import settings


def read_data():
    try:
        with open(settings.CONFIG_FILE, 'r') as f:
            return json.loads(f.read())
    except (FileNotFoundError, IOError):
        return {}


BOOL_CHOICES = [('true', 'Enabled'), ('false', 'Disabled')]
CURRENCY_CHOICES = [('INR', 'INR'), ('USD', 'USD')]
PAYMENT_TYPE_CHOICES = [('TEST', 'TEST'), ('LIVE', 'LIVE')]
PAYMENT_MODE_CHOICES = [
    ('all', 'all'), ('cards', 'cards'), ('netBanking', 'netBanking'),
    ('UPI', 'UPI'), ('imps', 'imps'), ('wallets', 'wallets'),
    ('cashCards', 'cashCards'), ('NEFTRTGS', 'NEFTRTGS'), ('emiBanks', 'emiBanks'),
]
TRANSACTION_TYPE_CHOICES = [('SALE', 'SALE')]
TRANSACTION_KIND_CHOICES = [('eMandate', 'eMandate'), ('SIonCards', 'SI on Cards')]


class AdminForm(forms.Form):
    merchantCode = forms.CharField(label='*Merchant Code', max_length=200)
    merchantSchemeCode = forms.CharField(label='*Merchant Scheme Code', max_length=200)
    SALT = forms.CharField(label='*SALT', max_length=200)
    currency = forms.ChoiceField(label='*Currency', choices=CURRENCY_CHOICES)
    typeOfPayment = forms.ChoiceField(label='*Type of Payment', choices=PAYMENT_TYPE_CHOICES)
    primaryColor = forms.CharField(label='Primary Color', max_length=50, required=False)
    secondaryColor = forms.CharField(label='Secondary Color', max_length=50, required=False)
    buttonColor1 = forms.CharField(label='Button Color 1', max_length=50, required=False)
    buttonColor2 = forms.CharField(label='Button Color 2', max_length=50, required=False)
    logoURL = forms.CharField(label='Logo URL', max_length=500, required=False)
    enableExpressPay = forms.ChoiceField(label='Enable ExpressPay', choices=BOOL_CHOICES)
    separateCardMode = forms.ChoiceField(label='Separate Card Mode', choices=BOOL_CHOICES)
    enableNewWindowFlow = forms.ChoiceField(label='Enable New Window Flow', choices=BOOL_CHOICES)
    merchantMessage = forms.CharField(label='Merchant Message', max_length=500, required=False)
    disclaimerMessage = forms.CharField(label='Disclaimer Message', max_length=500, required=False)
    paymentMode = forms.ChoiceField(label='Payment Mode', choices=PAYMENT_MODE_CHOICES)
    paymentModeOrder = forms.CharField(label='Payment Mode Order', widget=forms.Textarea(attrs={'cols': 80, 'rows': 2}), required=False)
    enableInstrumentDeRegistration = forms.ChoiceField(label='Enable InstrumentDeRegistration', choices=BOOL_CHOICES)
    transactionType = forms.ChoiceField(label='Transaction Type', choices=TRANSACTION_TYPE_CHOICES)
    hideSavedInstruments = forms.ChoiceField(label='Hide SavedInstruments', choices=BOOL_CHOICES)
    saveInstrument = forms.ChoiceField(label='Save Instrument', choices=BOOL_CHOICES)
    displayTransactionMessageOnPopup = forms.ChoiceField(label='Display Transaction Message On Popup', choices=BOOL_CHOICES)
    embedPaymentGatewayOnPage = forms.ChoiceField(label='Embed Payment Gateway On Page', choices=BOOL_CHOICES)
    enableSI = forms.ChoiceField(label='Enable eMandate/SI', choices=BOOL_CHOICES)
    hideSIDetails = forms.ChoiceField(label='Hide SI Details', choices=BOOL_CHOICES)
    hideSIConfirmation = forms.ChoiceField(label='Hide SI Confirmation', choices=BOOL_CHOICES)
    expandSIDetails = forms.ChoiceField(label='Expand SI Details', choices=BOOL_CHOICES)
    enableDebitDay = forms.ChoiceField(label='Enable Debit Day', choices=BOOL_CHOICES)
    showSIResponseMsg = forms.ChoiceField(label='Show SI Response Msg', choices=BOOL_CHOICES)
    showSIConfirmation = forms.ChoiceField(label='Show SI Confirmation', choices=BOOL_CHOICES)
    enableTxnForNonSICards = forms.ChoiceField(label='Enable Txn For NonSI Cards', choices=BOOL_CHOICES)
    showAllModesWithSI = forms.ChoiceField(label='Show All Modes With SI', choices=BOOL_CHOICES)


class OfflineVerificationForm(forms.Form):
    merchantTxnId = forms.CharField(label='Merchant Ref No')
    date = forms.DateField(label='Date', widget=forms.DateInput(attrs={'type': 'date'}))


class RefundForm(forms.Form):
    token = forms.CharField(label='TPSL Transaction ID')
    amount = forms.CharField(label='Amount')
    date = forms.DateField(label='Date', widget=forms.DateInput(attrs={'type': 'date'}))


class ReconciliationForm(forms.Form):
    merchantTxnId = forms.CharField(label='Merchant Ref No', widget=forms.Textarea)
    startDate = forms.DateField(label='From Date', widget=forms.DateInput(attrs={'type': 'date'}))
    endDate = forms.DateField(label='To Date', widget=forms.DateInput(attrs={'type': 'date'}))


class MandateVerificationForm(forms.Form):
    typeOfTransaction = forms.ChoiceField(label='Type of Transaction (eMandate/SI on Cards)', choices=TRANSACTION_KIND_CHOICES)
    merchantTxnId = forms.CharField(label='Merchant Transaction Id')
    customerId = forms.CharField(label='Consumer Id (Customer Id used during transaction)')
    date = forms.DateField(label='Date', widget=forms.DateInput(attrs={'type': 'date'}))


class TransactionSchedulingForm(forms.Form):
    typeOfTransaction = forms.ChoiceField(label='Type of Transaction (eMandate/SI on Cards)', choices=TRANSACTION_KIND_CHOICES)
    mandateRegId = forms.CharField(label='Mandate Registration Id')
    amount = forms.CharField(label='Amount')
    date = forms.DateField(label='Date', widget=forms.DateInput(attrs={'type': 'date'}))


class TransactionVerificationForm(forms.Form):
    typeOfTransaction = forms.ChoiceField(label='Type of Transaction (eMandate/SI on Cards)', choices=TRANSACTION_KIND_CHOICES)
    merchantTxnId = forms.CharField(label='Merchant Transaction Id (Transaction Id sent during transaction scheduling)')
    date = forms.DateField(label='Date', widget=forms.DateInput(attrs={'type': 'date'}))


class StopPaymentForm(forms.Form):
    tpslTransactionId = forms.CharField(label='TPSL Transaction Id (TPSL ID given in response of Transaction scheduling)')


class MandateDeactivationForm(forms.Form):
    typeOfTransaction = forms.ChoiceField(
        label='Type of Transaction (eMandate/SI on Cards)',
        choices=TRANSACTION_KIND_CHOICES,
        initial='SIonCards'
    )
    mandateRegId = forms.CharField(label='Mandate Registration Id')


class OnlineTransactionForm(forms.Form):
    merchantCode = forms.CharField(label='Merchant Code', required=False)
    txn_id = forms.CharField(label='Transaction ID', required=False)
    amount = forms.CharField(label='Amount', required=False)
    merchantSchemeCode = forms.CharField(label='Scheme', required=False)
    custID = forms.CharField(label='Customer Id', required=False)
    mobNo = forms.CharField(label='Mobile Number', required=False)
    email = forms.EmailField(label='Email', required=False)
    customerName = forms.CharField(label='Customer Name', required=False)
    currency = forms.CharField(label='Currency', required=False)
    SALT = forms.CharField(label='SALT', required=False)
    returnUrl = forms.CharField(label='Return URL', required=False)
    cardNumber = forms.CharField(widget=forms.HiddenInput, required=False)
    expMonth = forms.CharField(widget=forms.HiddenInput, required=False)
    expYear = forms.CharField(widget=forms.HiddenInput, required=False)
    cvvCode = forms.CharField(widget=forms.HiddenInput, required=False)
    siDetailsAtMerchantEndCond = forms.CharField(widget=forms.HiddenInput, required=False)
