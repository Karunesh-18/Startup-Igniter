// Razorpay Checkout (INR). The server creates the order/subscription and verifies the signature;
// this module only opens the payment window and relays the result.

import { createReportOrder, createSubscription, devActivate, verifyPayment } from './api';
import type { BillingMe } from './types';

interface RazorpayResponse {
  razorpay_payment_id: string;
  razorpay_signature: string;
  razorpay_order_id?: string;
  razorpay_subscription_id?: string;
}
interface RazorpayInstance {
  open(): void;
  on(event: 'payment.failed', cb: (r: { error: { description: string } }) => void): void;
}
declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => RazorpayInstance;
  }
}

let loading: Promise<void> | null = null;
function loadCheckout(): Promise<void> {
  if (window.Razorpay) return Promise.resolve();
  loading ??= new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = 'https://checkout.razorpay.com/v1/checkout.js';
    s.onload = () => resolve();
    s.onerror = () => {
      loading = null;
      reject(new Error('Could not load the payment window. Check your connection and try again.'));
    };
    document.head.appendChild(s);
  });
  return loading;
}

function open(options: Record<string, unknown>): Promise<RazorpayResponse | null> {
  return new Promise((resolve, reject) => {
    const rz = new window.Razorpay!({
      ...options,
      name: 'Startup Igniter',
      currency: 'INR',
      theme: { color: '#2d7ff9' },
      handler: (r: RazorpayResponse) => resolve(r),
      modal: { ondismiss: () => resolve(null) },
    });
    rz.on('payment.failed', (r) => reject(new Error(r.error.description || 'The payment failed.')));
    rz.open();
  });
}

/** Unlock one analysis's full report. Resolves true when paid and verified, false if the window was closed. */
export async function payForReport(billing: BillingMe, analysisId: string, email?: string): Promise<boolean> {
  if (billing.dev_mode && !billing.payments_enabled) {
    await devActivate({ kind: 'report', analysis_id: analysisId });
    return true;
  }
  const order = await createReportOrder(analysisId);
  await loadCheckout();
  const r = await open({
    key: order.key_id,
    order_id: order.order_id,
    amount: order.amount,
    description: 'Full report',
    prefill: { email },
  });
  if (!r) return false;
  await verifyPayment({ ...r, razorpay_order_id: order.order_id });
  return true;
}

/** Start the Pro subscription. */
export async function subscribePro(billing: BillingMe, email?: string): Promise<boolean> {
  if (billing.dev_mode && !billing.payments_enabled) {
    await devActivate({ kind: 'pro' });
    return true;
  }
  const sub = await createSubscription();
  await loadCheckout();
  const r = await open({
    key: sub.key_id,
    subscription_id: sub.subscription_id,
    description: 'Pro, monthly',
    prefill: { email },
  });
  if (!r) return false;
  await verifyPayment({ ...r, razorpay_subscription_id: sub.subscription_id });
  return true;
}
