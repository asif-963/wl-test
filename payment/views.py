from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .forms import (
    AdminForm, OfflineVerificationForm, RefundForm, ReconciliationForm,
    MandateVerificationForm, TransactionSchedulingForm, TransactionVerificationForm,
    StopPaymentForm, MandateDeactivationForm, OnlineTransactionForm, read_data
)
from datetime import datetime, timedelta, date
from django.conf import settings
import json
import requests
import hashlib
import random

string_to_bool = {'true': True, True: True, 'false': False, False: False}


def check_data():
    config_data = read_data()
    if (config_data.get('merchantCode', '') and config_data.get('SALT', '') and
            config_data.get('merchantSchemeCode', '') and config_data.get('currency', '')) == "":
        return False
    return config_data or False


def call_api(data):
    raw_response = requests.post(url='https://www.paynimo.com/api/paynimoV2.req', data=json.dumps(data))
    return raw_response.json()


def get_datastring(data):

    debit_start = ""
    debit_end = ""

    if data.get("debitStartDate"):
        debit_start = "-".join(reversed(data["debitStartDate"].split("-")))

    if data.get("debitEndDate"):
        debit_end = "-".join(reversed(data["debitEndDate"].split("-")))

    return (
        data.get("merchantCode", "") + "|" +
        data.get("txn_id", "") + "|" +
        data.get("amount", "") + "|" +
        data.get("accNo", "") + "|" +
        data.get("custID", "") + "|" +
        data.get("mobNo", "") + "|" +
        data.get("email", "") + "|" +
        debit_start + "|" +
        debit_end + "|" +
        data.get("maxAmount", "") + "|" +
        data.get("amountType", "") + "|" +
        data.get("frequency", "") + "|" +
        data.get("cardNumber", "") + "|" +
        data.get("expMonth", "") + "|" +
        data.get("expYear", "") + "|" +
        data.get("cvvCode", "") + "|" +
        data.get("SALT", "")
    )


def get_hash_object(hashed_data, data, config_data):
    prepared_object = {
        'tarCall': False,
        'features': {
            'showPGResponseMsg': True,
            'enableMerTxnDetails': True,
            'enableAbortResponse': False,
            'enableSI': string_to_bool[config_data['enableSI']],
            'siDetailsAtMerchantEnd': string_to_bool[config_data.get('siDetailsAtMerchantEnd', 'false')],
            'enableNewWindowFlow': string_to_bool[config_data['enableNewWindowFlow']],
            'enableExpressPay': string_to_bool[config_data['enableExpressPay']],
            'enableInstrumentDeRegistration': string_to_bool[config_data['enableInstrumentDeRegistration']],
            'hideSavedInstruments': string_to_bool[config_data['hideSavedInstruments']],
            'separateCardMode': string_to_bool[config_data['separateCardMode']],
            'payWithSavedInstrument': string_to_bool[config_data['saveInstrument']],
            'hideSIDetails': string_to_bool[config_data['hideSIDetails']],
            'hideSIConfirmation': string_to_bool[config_data['hideSIConfirmation']],
            'expandSIDetails': string_to_bool[config_data['expandSIDetails']],
            'enableDebitDay': string_to_bool[config_data['enableDebitDay']],
            'showSIResponseMsg': string_to_bool[config_data['showSIResponseMsg']],
            'showSIConfirmation': string_to_bool[config_data['showSIConfirmation']],
            'enableTxnForNonSICards': string_to_bool[config_data['enableTxnForNonSICards']],
            'showAllModesWithSI': string_to_bool[config_data['showAllModesWithSI']],
        },
        'consumerData': {
            'deviceId': 'WEBSH2',
            'token': hashed_data,
            'returnUrl': data['returnUrl'],
            'paymentMode': config_data['paymentMode'],
            'paymentModeOrder': config_data['paymentModeOrder'].replace(' ', '').split(','),
            'checkoutElement': '#worldline_embeded_popup' if string_to_bool[config_data['embedPaymentGatewayOnPage']] else '',
            'merchantLogoUrl': config_data['logoURL'],
            'merchantId': data['merchantCode'],
            'merchantMsg': config_data['merchantMessage'],
            'disclaimerMsg': config_data['disclaimerMessage'],
            'currency': data['currency'],
            'consumerId': data['custID'],
            'consumerMobileNo': data['mobNo'],
            'consumerEmailId': data['email'],
            'txnId': data['txn_id'],
            'items': [{'itemId': data['merchantSchemeCode'], 'amount': data['amount'], 'comAmt': '0'}],
            'customStyle': {
                'PRIMARY_COLOR_CODE': config_data['primaryColor'],
                'SECONDARY_COLOR_CODE': config_data['secondaryColor'],
                'BUTTON_COLOR_CODE_1': config_data['buttonColor1'],
                'BUTTON_COLOR_CODE_2': config_data['buttonColor2'],
            }
        }
    }
    if string_to_bool[data.get('siDetailsAtMerchantEndCond', 'false')]:

        prepared_object['consumerData']['accountNo'] = data.get('accNo', '')
        prepared_object['consumerData']['accountHolderName'] = data.get('accountHolderName', '')
        prepared_object['consumerData']['ifscCode'] = data.get('ifscCode', '')
        prepared_object['consumerData']['accountType'] = data.get('accountType', '')

        if data.get('debitStartDate'):
            prepared_object['consumerData']['debitStartDate'] = "-".join(reversed(data['debitStartDate'].split('-')))

        if data.get('debitEndDate'):
            prepared_object['consumerData']['debitEndDate'] = "-".join(reversed(data['debitEndDate'].split('-')))

        prepared_object['consumerData']['maxAmount'] = data.get('maxAmount', '')
        prepared_object['consumerData']['amountType'] = data.get('amountType', '')
        prepared_object['consumerData']['frequency'] = data.get('frequency', '')

    elif string_to_bool[config_data['enableSI']]:

        if data.get('debitStartDate'):
            prepared_object['consumerData']['debitStartDate'] = "-".join(reversed(data['debitStartDate'].split('-')))

        if data.get('debitEndDate'):
            prepared_object['consumerData']['debitEndDate'] = "-".join(reversed(data['debitEndDate'].split('-')))

        prepared_object['consumerData']['maxAmount'] = data.get('maxAmount', '')
        prepared_object['consumerData']['amountType'] = data.get('amountType', '')
        prepared_object['consumerData']['frequency'] = data.get('frequency', '')

    return prepared_object


def admin_view(request):
    config_data = read_data()
    if request.method == 'POST':
        form = AdminForm(request.POST)
        if form.is_valid():
            request_data = form.cleaned_data
            with open(settings.CONFIG_FILE, 'w') as f:
                json.dump(request_data, f, indent=4)
            messages.success(request, 'Success: Information has been updated.')
            return redirect('admin_view')
    else:
        form = AdminForm(initial=config_data)
    return render(request, 'admin.html', {'form': form, 'config_data': config_data})


def online_transaction(request):

    config_data = check_data()

    if not config_data:
        return render(request, "mandatory_fields_page_error.html")

    start_date = date.today().strftime("%Y-%m-%d")
    end_date = (date.today() + timedelta(days=30 * 365.2425)).strftime("%Y-%m-%d")


    return_url = (
    request.build_absolute_uri(reverse("response"))
    if not string_to_bool[config_data["displayTransactionMessageOnPopup"]]
    else ""
    )

    print("\n==============================")
    print("RETURN URL :", return_url)
    print("==============================")

    si_at_merchant = (
        "true"
        if (
            string_to_bool[config_data["enableSI"]]
            and string_to_bool[
                config_data.get("siDetailsAtMerchantEnd", "false")
            ]
        )
        else "false"
    )

    # ===========================
    # POST
    # ===========================

    if request.method == "POST":

        form_data = request.POST.dict()
        form_data.pop("csrfmiddlewaretoken", None)

        # Merchant Details
        form_data["merchantCode"] = config_data["merchantCode"]
        form_data["merchantSchemeCode"] = config_data["merchantSchemeCode"]
        form_data["currency"] = config_data["currency"]
        form_data["SALT"] = config_data["SALT"]

        form_data["txn_id"] = str(random.randint(100000000, 999999999))
        form_data["returnUrl"] = return_url

        # User Details
        form_data["custID"] = (
            form_data.get("custID")
            or form_data.get("customerName")
            or form_data.get("customer_name")
            or ""
        )

        form_data["mobNo"] = (
            form_data.get("mobNo")
            or form_data.get("mobile")
            or ""
        )

        form_data["email"] = form_data.get("email", "")

        # Test Merchant
        if config_data["typeOfPayment"] == "TEST":
            form_data["amount"] = "1"

        # Optional Fields
        defaults = [
            "accNo",
            "accountType",
            "accountHolderName",
            "aadharNo",
            "ifscCode",
            "debitStartDate",
            "debitEndDate",
            "maxAmount",
            "amountType",
            "frequency",
            "cardNumber",
            "expMonth",
            "expYear",
            "cvvCode",
        ]

        for field in defaults:
            form_data.setdefault(field, "")

        form_data.setdefault(
            "siDetailsAtMerchantEndCond",
            si_at_merchant
        )

        # Generate Hash
        data_string = get_datastring(form_data)

        hashed_data = hashlib.sha512(
            data_string.encode("utf-8")
        ).hexdigest()

        print("\n==============================")
        print("Merchant Code :", form_data["merchantCode"])
        print("Scheme Code   :", form_data["merchantSchemeCode"])
        print("Customer ID   :", form_data["custID"])
        print("Mobile        :", form_data["mobNo"])
        print("Email         :", form_data["email"])
        print("Amount        :", form_data["amount"])
        print("==============================")

        print("\nDATA STRING")
        print(data_string)

        print("\nHASH")
        print(hashed_data)

        data = get_hash_object(
            hashed_data,
            form_data,
            config_data
        )

        return JsonResponse(data)

    # ===========================
    # GET
    # ===========================

    initial = {
        "merchantCode": config_data["merchantCode"],
        "merchantSchemeCode": config_data["merchantSchemeCode"],
        "currency": config_data["currency"],
        "SALT": config_data["SALT"],
        "txn_id": str(random.randint(100000000, 999999999)),
        "returnUrl": return_url,
        "siDetailsAtMerchantEndCond": si_at_merchant,
    }

    form = OnlineTransactionForm(initial=initial)

    return render(
        request,
        "online_transaction.html",
        {
            "form": form,
            "config_data": config_data,
            "start_date": start_date,
            "end_date": end_date,
        },
    )
    
@csrf_exempt
@csrf_exempt
def response_view(request):

    print("\n========== WORLDLINE RESPONSE ==========")
    print("METHOD :", request.method)
    print("POST   :", dict(request.POST))
    print("GET    :", dict(request.GET))
    print("BODY   :", request.body.decode("utf-8", errors="ignore"))
    print("========================================\n")

    data = [""] * 16
    full_response = ""
    api_response = {}

    if request.method == "POST":

        # Worldline generally returns the response in "msg"
        full_response = request.POST.get("msg", "")

        # If msg is not present, try raw body
        if not full_response:
            full_response = request.body.decode("utf-8", errors="ignore")

        print("FULL RESPONSE :", full_response)

        if full_response:

            temp = full_response.split("|")

            for i in range(min(len(temp), 16)):
                data[i] = temp[i]

            print("SPLIT DATA :", temp)

            # Success
            if data[0] == "0300":

                config_data = check_data()

                if config_data:

                    request_data = {
                        "merchant": {
                            "identifier": config_data["merchantCode"]
                        },
                        "transaction": {
                            "deviceIdentifier": "S",
                            "currency": config_data["currency"],
                            "dateTime": data[8].split()[0] if data[8] else "",
                            "token": data[5],
                            "requestType": "S",
                        },
                    }

                    print("VERIFY REQUEST")
                    print(json.dumps(request_data, indent=4))

                    try:
                        api_response = call_api(request_data)
                        print("VERIFY RESPONSE")
                        print(api_response)
                    except Exception as e:
                        print("API ERROR :", e)

    context = {
        "status": data[0],
        "message": data[1],
        "error": data[2],
        "clientTxnRef": data[3],
        "bankCode": data[4],
        "tpslTxnId": data[5],
        "amount": data[6],
        "clientMeta": data[7],
        "txnTime": data[8],
        "balance": data[9],
        "cardId": data[10],
        "alias": data[11],
        "bankTxnId": data[12],
        "mandate": data[13],
        "token": data[14],
        "hash": data[15],
        "response": api_response,
        "full_response": full_response,
    }

    return render(request, "response.html", context)

def offline_verification(request):
    config_data = check_data()

    if not config_data:
        return render(request, "mandatory_fields_page_error.html")

    form = OfflineVerificationForm(request.POST or None)

    api_response = {}

    if request.method == "POST" and form.is_valid():

        data = {
            "merchant": {
                "identifier": config_data["merchantCode"]
            },
            "transaction": {
                "deviceIdentifier": "S",
                "currency": config_data["currency"],
                "identifier": form.cleaned_data["merchantTxnId"],
                "dateTime": form.cleaned_data["date"].strftime("%d-%m-%Y"),
                "requestType": "O",
            },
        }

        api_response = call_api(data)

    return render(
        request,
        "offline_verification.html",
        {
            "form": form,
            "response": api_response,
        },
    )

def refund(request):
    config_data = check_data()
    if not config_data:
        return render(request, 'mandatory_fields_page_error.html')
    form = RefundForm(request.POST or None)
    api_response = {}
    if request.method == 'POST' and form.is_valid():
        data = {
            'merchant': {'identifier': config_data['merchantCode']},
            'cart': {},
            'transaction': {
                'deviceIdentifier': 'S',
                'amount': form.cleaned_data['amount'],
                'currency': config_data['currency'],
                'token': form.cleaned_data['token'],
                'dateTime': form.cleaned_data['date'].strftime('%d-%m-%Y'),
                'requestType': 'R'
            }
        }
        api_response = call_api(data)
    return render(request, 'refund.html', {'form': form, 'response': api_response})


def reconciliation(request):
    config_data = check_data()
    if not config_data:
        return render(request, 'mandatory_fields_page_error.html')
    form = ReconciliationForm(request.POST or None)
    last_response = []
    if request.method == 'POST' and form.is_valid():
        transaction_ids = form.cleaned_data['merchantTxnId'].strip(', ')
        transaction_ids = ''.join(transaction_ids.split())
        start_dt = form.cleaned_data['startDate']
        end_dt = form.cleaned_data['endDate']
        delta = end_dt - start_dt
        for transaction_id in transaction_ids.split(','):
            count = 0
            resp = {}
            for i in range(delta.days + 1):
                day = start_dt + timedelta(days=i)
                date_str = day.strftime('%d-%m-%Y')
                data = {
                    'merchant': {'identifier': config_data['merchantCode']},
                    'transaction': {
                        'deviceIdentifier': 'S',
                        'currency': config_data['currency'],
                        'identifier': transaction_id,
                        'dateTime': date_str,
                        'requestType': 'O'
                    }
                }
                resp = call_api(data)
                if (resp['paymentMethod']['paymentTransaction']['statusCode'] != 9999 and
                        resp['paymentMethod']['paymentTransaction']['errorMessage'] != 'Transactionn Not Found'):
                    count = 1
                    last_response.append(resp)
                    break
            if count == 0:
                last_response.append(resp)
    return render(request, 'reconciliation.html', {'form': form, 'last_response': last_response})


def s2s(request):
    config_data = check_data()
    if not config_data:
        return render(request, 'mandatory_fields_page_error.html')
    data = request.GET.get('msg', '').split('|')
    clnt_txn_ref = data[3] if len(data) > 3 else ''
    pg_txn_id = data[5] if len(data) > 5 else ''
    data_string = '|'.join(data[:-1]) + '|' + config_data['SALT']
    result = hashlib.sha512(data_string.encode())
    status = 1 if (data and data[-1] == result.hexdigest()) else 0
    return render(request, 's2s.html', {'clnt_txn_ref': clnt_txn_ref, 'pg_txn_id': pg_txn_id, 'status': status})


def mandate_verification(request):
    config_data = check_data()
    if not config_data:
        return render(request, 'mandatory_fields_page_error.html')
    form = MandateVerificationForm(request.POST or None)
    api_response = {}
    if request.method == 'POST' and form.is_valid():
        type_data = '002' if form.cleaned_data['typeOfTransaction'] == 'eMandate' else '001'
        data = {
            'merchant': {'identifier': config_data['merchantCode']},
            'payment': {'instruction': {}},
            'transaction': {
                'deviceIdentifier': 'S',
                'type': type_data,
                'currency': config_data['currency'],
                'identifier': form.cleaned_data['merchantTxnId'],
                'dateTime': form.cleaned_data['date'].strftime('%d-%m-%Y'),
                'subType': '002',
                'requestType': 'TSI'
            },
            'consumer': {'identifier': form.cleaned_data['customerId']}
        }
        api_response = call_api(data)
    return render(request, 'mandate_verification.html', {'form': form, 'response': api_response})


def transaction_scheduling(request):
    config_data = check_data()
    if not config_data:
        return render(request, 'mandatory_fields_page_error.html')
    form = TransactionSchedulingForm(request.POST or None)
    api_response = {}
    if request.method == 'POST' and form.is_valid():
        transaction_id = str(random.randint(100, 9999999999))
        date_str = form.cleaned_data['date'].strftime('%d%m%Y')
        type_data = '002' if form.cleaned_data['typeOfTransaction'] == 'eMandate' else '001'
        data = {
            'merchant': {'identifier': config_data['merchantCode']},
            'payment': {
                'instrument': {'identifier': config_data['merchantSchemeCode']},
                'instruction': {
                    'amount': form.cleaned_data['amount'],
                    'endDateTime': date_str,
                    'identifier': form.cleaned_data['mandateRegId']
                }
            },
            'transaction': {
                'deviceIdentifier': 'S',
                'type': type_data,
                'currency': config_data['currency'],
                'identifier': transaction_id,
                'subType': '003',
                'requestType': 'TSI'
            }
        }
        api_response = call_api(data)
    return render(request, 'transaction_scheduling.html', {'form': form, 'response': api_response})


def transaction_verification(request):
    config_data = check_data()
    if not config_data:
        return render(request, 'mandatory_fields_page_error.html')
    form = TransactionVerificationForm(request.POST or None)
    api_response = {}
    if request.method == 'POST' and form.is_valid():
        type_data = '002' if form.cleaned_data['typeOfTransaction'] == 'eMandate' else '001'
        data = {
            'merchant': {'identifier': config_data['merchantCode']},
            'payment': {'instruction': {}},
            'transaction': {
                'deviceIdentifier': 'S',
                'type': type_data,
                'currency': config_data['currency'],
                'identifier': form.cleaned_data['merchantTxnId'],
                'dateTime': form.cleaned_data['date'].strftime('%d-%m-%Y'),
                'subType': '004',
                'requestType': 'TSI'
            }
        }
        api_response = call_api(data)
        if api_response:
            msg = api_response['paymentMethod']['paymentTransaction']['statusMessage']
            if msg == 'I':
                api_response['paymentMethod']['paymentTransaction']['statusMessage'] = 'Initiated'
            elif msg == 'D':
                api_response['paymentMethod']['paymentTransaction']['statusMessage'] = 'Success'
            elif msg == 'F':
                api_response['paymentMethod']['paymentTransaction']['statusMessage'] = 'Failure'
    return render(request, 'transaction_verification.html', {'form': form, 'response': api_response})


def stop_payment(request):
    config_data = check_data()
    if not config_data:
        return render(request, 'mandatory_fields_page_error.html')
    form = StopPaymentForm(request.POST or None)
    api_response = {}
    if request.method == 'POST' and form.is_valid():
        transaction_id = str(random.randint(100, 9999999999))
        data = {
            'merchant': {'webhookEndpointURL': '', 'responseType': '', 'responseEndpointURL': '',
                         'description': '', 'identifier': config_data['merchantCode'], 'webhookType': ''},
            'cart': {'item': [{'description': '', 'providerIdentifier': '', 'surchargeOrDiscountAmount': '',
                               'amount': '', 'comAmt': '', 'sKU': '', 'reference': '', 'identifier': ''}],
                     'reference': '', 'identifier': '', 'description': '', 'Amount': ''},
            'payment': {
                'method': {'token': '', 'type': ''},
                'instrument': {'expiry': {'year': '', 'month': '', 'dateTime': ''}, 'provider': '',
                               'iFSC': '', 'holder': {'name': '', 'address': {'country': '', 'street': '',
                               'state': '', 'city': '', 'zipCode': '', 'county': ''}},
                               'bIC': '', 'type': '', 'action': '', 'mICR': '', 'verificationCode': '',
                               'iBAN': '', 'processor': '', 'issuance': {'year': '', 'month': '', 'dateTime': ''},
                               'alias': '', 'identifier': config_data['merchantSchemeCode'], 'token': '',
                               'authentication': {'token': '', 'type': '', 'subType': ''},
                               'subType': '', 'issuer': '', 'acquirer': ''},
                'instruction': {'occurrence': '', 'amount': '11', 'frequency': '', 'type': '',
                                'description': '', 'action': '', 'limit': '', 'endDateTime': '',
                                'identifier': '', 'reference': '', 'startDateTime': '', 'validity': ''}
            },
            'transaction': {
                'deviceIdentifier': 'S', 'smsSending': '', 'amount': '', 'forced3DSCall ': '',
                'type': '001', 'description': '', 'currency': config_data['currency'],
                'isRegistration': '', 'identifier': transaction_id, 'dateTime': '',
                'token': form.cleaned_data['tpslTransactionId'], 'securityToken': '',
                'subType': '006', 'requestType': 'TSI', 'reference': '',
                'merchantInitiated': '', 'merchantRefNo': ''
            },
            'consumer': {'mobileNumber': '', 'emailID': '', 'identifier': '', 'accountNo': ''}
        }
        api_response = call_api(data)
    return render(request, 'stop_payment.html', {'form': form, 'response': api_response})


def mandate_deactivation(request):
    config_data = check_data()
    if not config_data:
        return render(request, 'mandatory_fields_page_error.html')
    form = MandateDeactivationForm(request.POST or None)
    api_response = {}
    if request.method == 'POST' and form.is_valid():
        type_data = '002' if form.cleaned_data['typeOfTransaction'] == 'eMandate' else '001'
        transaction_id = str(random.randint(100, 9999999999))
        data = {
            'merchant': {'webhookEndpointURL': '', 'responseType': '', 'responseEndpointURL': '',
                         'description': '', 'identifier': config_data['merchantCode'], 'webhookType': ''},
            'cart': {'item': [{'description': '', 'providerIdentifier': '', 'surchargeOrDiscountAmount': '',
                               'amount': '', 'comAmt': '', 'sKU': '', 'reference': '', 'identifier': ''}],
                     'reference': '', 'identifier': '', 'description': '', 'Amount': ''},
            'payment': {
                'method': {'token': '', 'type': ''},
                'instrument': {'expiry': {'year': '', 'month': '', 'dateTime': ''}, 'provider': '',
                               'iFSC': '', 'holder': {'name': '', 'address': {'country': '', 'street': '',
                               'state': '', 'city': '', 'zipCode': '', 'county': ''}},
                               'bIC': '', 'type': '', 'action': '', 'mICR': '', 'verificationCode': '',
                               'iBAN': '', 'processor': '', 'issuance': {'year': '', 'month': '', 'dateTime': ''},
                               'alias': '', 'identifier': '', 'token': '',
                               'authentication': {'token': '', 'type': '', 'subType': ''},
                               'subType': '', 'issuer': '', 'acquirer': ''},
                'instruction': {'occurrence': '', 'amount': '', 'frequency': '', 'type': '',
                                'description': '', 'action': '', 'limit': '', 'endDateTime': '',
                                'identifier': '', 'reference': '', 'startDateTime': '', 'validity': ''}
            },
            'transaction': {
                'deviceIdentifier': 'S', 'smsSending': '', 'amount': '', 'forced3DSCall ': '',
                'type': type_data, 'description': '', 'currency': config_data['currency'],
                'isRegistration': '', 'identifier': transaction_id, 'dateTime': '',
                'token': form.cleaned_data['mandateRegId'], 'securityToken': '',
                'subType': '005', 'requestType': 'TSI', 'reference': '',
                'merchantInitiated': '', 'merchantRefNo': ''
            },
            'consumer': {'mobileNumber': '', 'emailID': '', 'identifier': '', 'accountNo': ''}
        }
        api_response = call_api(data)
        if api_response:
            if (api_response['paymentMethod']['paymentTransaction']['statusCode'] == "" and
                    api_response['paymentMethod']['error']['desc'] == ""):
                api_response['paymentMethod']['paymentTransaction']['statusCode'] = "Not Found"
                api_response['paymentMethod']['error']['desc'] = "Not Found"
    return render(request, 'mandate_deactivation.html', {'form': form, 'response': api_response})
