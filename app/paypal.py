from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional
import os
from .functions import b64, is_uuid_like
from .databases import sql_connection
import aiohttp
from .logger import log_warning, log_info

PAYPAL_ENDPOINT = os.getenv('PAYPAL_ENDPOINT')
PAYPAL_ITEMCODE_100MESSAGES = os.getenv('PAYPAL_ITEMCODE_100MESSAGES')
PAYPAL_ITEMCODE_RECHARGEFREQUENCY = os.getenv('PAYPAL_ITEMCODE_RECHARGEFREQUENCY')
PAYPAL_ITEMCODE_RECHARGELIMIT = os.getenv('PAYPAL_ITEMCODE_RECHARGELIMIT')
PAYPAL_APP_CLIENTID = os.getenv('PAYPAL_APP_CLIENTID')
PAYPAL_APP_SECRET = os.getenv('PAYPAL_APP_SECRET')
PAYPAL_WEBHOOK_ENDPOINT = os.getenv('PAYPAL_WEBHOOK_ENDPOINT')
ENABLE_PAYPAL = os.getenv('ENABLE_PAYPAL') == 'true'

if ENABLE_PAYPAL and not all([PAYPAL_APP_SECRET, PAYPAL_APP_CLIENTID, PAYPAL_ITEMCODE_RECHARGELIMIT, PAYPAL_ITEMCODE_RECHARGEFREQUENCY, PAYPAL_ITEMCODE_100MESSAGES, PAYPAL_ENDPOINT]):
    raise Exception("Missing PAYPAL environment variables")

PAYPAL_BASE_AUTH = b64(PAYPAL_APP_CLIENTID + ":" + PAYPAL_APP_SECRET)

class PayPalAmountModel(BaseModel):
    currency_code: str
    value: str

class PayPalDisputeCategory(str, Enum):
    ITEM_NOT_RECEIVED = "ITEM_NOT_RECEIVED"
    UNAUTHORIZED_TRANSACTION = "UNAUTHORIZED_TRANSACTION"
    MERCHANDISE_OR_SERVICE_NOT_RECEIVED = "MERCHANDISE_OR_SERVICE_NOT_RECEIVED"
    MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED = "MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED"

class PayPalSellerProtectionStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    PARTIALLY_ELIGIBLE = "PARTIALLY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"

class PayPalSellerProtectionModel(BaseModel):
    status: PayPalSellerProtectionStatus
    dispute_categories: List[PayPalDisputeCategory]

class PayPalRelatedIdsModel(BaseModel):
    order_id: str

class PayPalSupplementaryDataModel(BaseModel):
    related_ids: PayPalRelatedIdsModel

class PayPalPayeeModel(BaseModel):
    merchant_id: str

class PayPalPlatformFeeModel(BaseModel):
    amount: PayPalAmountModel
    payee: PayPalPayeeModel

class PayPalSellerReceivableBreakdownModel(BaseModel):
    gross_amount: PayPalAmountModel
    paypal_fee: PayPalAmountModel
    platform_fees: Optional[List[PayPalPlatformFeeModel]] = None
    net_amount: PayPalAmountModel

class PayPalLinkModel(BaseModel):
    href: str
    rel: str
    method: str
    encType: Optional[str] = None

class PayPalDisbursementMode(str, Enum):
    INSTANT = "INSTANT"
    DELAYED = "DELAYED"

class PayPalCaptureStatus(str, Enum):
    COMPLETED = "COMPLETED"
    DECLINED = "DECLINED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    PENDING = "PENDING"
    REFUNDED = "REFUNDED"

class PayPalCaptureResourceModel(BaseModel):
    disbursement_mode: PayPalDisbursementMode
    amount: PayPalAmountModel
    seller_protection: PayPalSellerProtectionModel
    supplementary_data: PayPalSupplementaryDataModel
    update_time: datetime
    create_time: datetime
    final_capture: bool
    seller_receivable_breakdown: PayPalSellerReceivableBreakdownModel
    invoice_id: Optional[str] = None
    links: List[PayPalLinkModel]
    id: str
    status: PayPalCaptureStatus

class PayPalWebhookEvent(BaseModel):
    id: str
    create_time: datetime
    resource_type: str
    event_type: str
    summary: str
    resource: PayPalCaptureResourceModel
    links: List[PayPalLinkModel]
    event_version: str
    resource_version: str

async def login()->str:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://{PAYPAL_ENDPOINT}/v1/oauth2/token", headers={
            'Authorization': f"Basic {PAYPAL_BASE_AUTH}",
            'Content-Type': 'application/x-www-form-urlencoded',
        }, params=(
            ('grant_type', 'client_credentials'),
        )) as response:
            response.raise_for_status()
            access_token = response.json()['access_token']
            if not access_token:
                raise Exception('Invalid access token')
            return access_token

async def handle_transactions(params: tuple):
    access_token = await login()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://{PAYPAL_ENDPOINT}/v1/reporting/transactions", headers={
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json',
        }, params=params) as response:
            response.raise_for_status()
            for transaction in response.json():
                sql_connection.ping()
                cursor = sql_connection.cursor()
                cursor.execute("SELECT 1 FROM purchases WHERE paypal_transaction_id=?", [transaction['transaction_info']['transaction_id']])
                user_id = str(transaction['transaction_info']['custom_field']).strip(' ')
                if cursor.fetchone():
                    continue
                if is_uuid_like(user_id):
                    sql_connection.ping()
                    cursor = sql_connection.cursor()
                    cursor.execute("SELECT user_id FROM chat_users.users WHERE user_id=?", [user_id])
                    found = False
                    for row in cursor:
                        found = True
                    if not found:
                        log_warning(f"User {user_id} not found for transaction {transaction['transaction_info']['transaction_id']}")
                        continue
                    for item in transaction['cart_info']['item_details']:
                        item['item_quantity'] = int(item['item_quantity'])
                        if item['item_quantity'] > 0:
                            sql_connection.ping()
                            if item['item_code'] == PAYPAL_ITEMCODE_100MESSAGES:
                                log_info('FOUND 100MESSAGES in transaction')
                                sql_connection.cursor().execute("INSERT INTO purchases (user_id, at_datetime, amount, product, paypal_transaction_id) VALUES (?, ? ,?, ?, ?)", [
                                    user_id,
                                    transaction['transaction_info']['transaction_initiation_date'],
                                    item['item_quantity'] or 1,
                                    '100MESSAGES',
                                    transaction['transaction_info']['transaction_id']
                                ])
                                sql_connection.cursor().execute("UPDATE chat_users.users SET additional_remaining_messages=additional_remaining_messages+100 WHERE user_id=?", [user_id])
                            elif item['item_code'] == PAYPAL_ITEMCODE_RECHARGEFREQUENCY:
                                log_info('FOUND RECHARGEFREQUENCY in transaction')
                                sql_connection.cursor().execute("INSERT INTO purchases (user_id, at_datetime, amount, product, paypal_transaction_id) VALUES (?, ? ,?, ?, ?)", [
                                    user_id,
                                    transaction['transaction_info']['transaction_initiation_date'],
                                    item['item_quantity'] or 1,
                                    'RECHARGEFREQUENCY',
                                    transaction['transaction_info']['transaction_id']
                                ])
                                for i in range(item['item_quantity']):
                                    sql_connection.cursor().execute("INSERT INTO chat_users.subscriptions (user_id, product, from_datetime, to_datetime) VALUES (?, ?, Now(), NOW() + 86400*30)", [user_id, 'RECHARGEFREQUENCY'])
                            elif item['item_code'] == PAYPAL_ITEMCODE_RECHARGELIMIT:
                                log_info('FOUND RECHARGELIMIT in transaction')
                                sql_connection.cursor().execute("INSERT INTO purchases (user_id, at_datetime, amount, product, paypal_transaction_id) VALUES (?, ? ,?, ?, ?)", [
                                    user_id,
                                    transaction['transaction_info']['transaction_initiation_date'],
                                    item['item_quantity'] or 1,
                                    'RECHARGELIMIT',
                                    transaction['transaction_info']['transaction_id']
                                ])
                                for i in range(item['item_quantity']):
                                    sql_connection.cursor().execute("INSERT INTO chat_users.subscriptions (user_id, product, from_datetime, to_datetime) VALUES (?, ?, Now(), NOW() + 86400*30)", [user_id, 'RECHARGELIMIT'])
                            else:
                                log_warning(f"Item {item['item_code']} not found for transaction {transaction['transaction_info']['transaction_id']}")
