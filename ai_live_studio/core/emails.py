"""
Official branded transactional emails for account/payment lifecycle
events — welcome after registration, deposit pending, deposit approved,
deposit rejected. Each is sent to the exact email address the user
registered with.

Uses Django's standard EMAIL_BACKEND (console locally, real SMTP/your
provider once configured in production) via EmailMultiAlternatives, so
every email has a clean HTML version with a plain-text fallback for
clients that don't render HTML.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def _email_shell(title, body_html, cta_url=None, cta_label=None):
    """Wraps body content in a simple branded HTML email shell matching
    the site's teal/copper theme."""
    cta_block = ''
    if cta_url and cta_label:
        cta_block = f'''
        <tr>
          <td style="padding: 8px 0 28px;">
            <a href="{cta_url}"
               style="display:inline-block; background:linear-gradient(135deg,#14b8a6,#c2793d);
                      color:#ffffff; text-decoration:none; padding:12px 28px;
                      border-radius:8px; font-weight:600; font-size:14px;">
              {cta_label}
            </a>
          </td>
        </tr>'''

    return f'''
    <html>
    <body style="margin:0; padding:0; background:#0a0f0f; font-family:-apple-system,'Segoe UI',Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0f0f; padding:40px 16px;">
        <tr>
          <td align="center">
            <table width="480" cellpadding="0" cellspacing="0"
                   style="background:#0e1615; border:1px solid #1f2b2a; border-radius:16px; overflow:hidden;">
              <tr>
                <td style="padding:28px 32px 0;">
                  <div style="font-size:20px; font-weight:800;
                              background:linear-gradient(135deg,#14b8a6,#c2793d);
                              -webkit-background-clip:text; background-clip:text; color:#14b8a6;">
                    {settings.SITE_NAME}
                  </div>
                </td>
              </tr>
              <tr>
                <td style="padding:20px 32px 8px;">
                  <h2 style="color:#eef2f1; font-size:19px; margin:0 0 16px;">{title}</h2>
                  <div style="color:#97a3a1; font-size:14px; line-height:1.7;">{body_html}</div>
                </td>
              </tr>
              {cta_block}
              <tr>
                <td style="padding:20px 32px 28px; border-top:1px solid #1f2b2a;">
                  <p style="color:#667370; font-size:12px; margin:16px 0 0;">
                    This is an official message from {settings.SITE_NAME}. If you didn't
                    expect this email, you can safely ignore it.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    '''


def _send(subject, plain_text, html_body, recipient):
    if not recipient:
        return
    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
    except Exception:
        # Never let an email failure break the user-facing flow
        # (registration, payment submission, admin approval) — just log it.
        logger.exception('Failed to send email "%s" to %s', subject, recipient)


def send_welcome_email(user, verify_url):
    subject = f'Welcome to {settings.SITE_NAME}, {user.display_name}!'
    plain_text = (
        f'Hi {user.display_name},\n\n'
        f'Welcome to {settings.SITE_NAME} — real-time AI-powered live streaming.\n\n'
        f'Please verify your email to activate your account:\n{verify_url}\n\n'
        f'Once verified, log in and choose a plan to unlock your dashboard and '
        f'start streaming with your own AI look.\n\n'
        f'This link expires in 24 hours.\n\n'
        f'— The {settings.SITE_NAME} Team'
    )
    body_html = f'''
      <p>Hi {user.display_name},</p>
      <p>Welcome to <strong>{settings.SITE_NAME}</strong> — real-time,
      AI-powered live streaming. We're glad you're here.</p>
      <p>Please verify your email address to activate your account.
      Once verified, log in and choose a plan to unlock your dashboard
      and start streaming with your own AI look.</p>
      <p style="color:#667370; font-size:12px;">This link expires in 24 hours.</p>
    '''
    html_body = _email_shell('Welcome aboard 🎉', body_html, cta_url=verify_url, cta_label='Verify My Email')
    _send(subject, plain_text, html_body, user.email)


def send_deposit_pending_email(submission):
    plan_name = submission.plan.name if submission.plan else 'selected'
    subject = f'Payment received — under review ({settings.SITE_NAME})'
    plain_text = (
        f'Hi {submission.user.display_name},\n\n'
        f'We\'ve received your payment submission for the "{plan_name}" plan '
        f'(${submission.amount}).\n\n'
        f'Your payment is now pending review by our team. You\'ll receive '
        f'another email as soon as it\'s approved and your credits are added.\n\n'
        f'— The {settings.SITE_NAME} Team'
    )
    body_html = f'''
      <p>Hi {submission.user.display_name},</p>
      <p>We've received your payment submission for the
      <strong>{plan_name}</strong> plan (${submission.amount}).</p>
      <p>Your payment is now <strong style="color:#d99a3d;">pending review</strong>
      by our team. You'll receive another email as soon as it's approved
      and your credits are added to your account — this usually doesn't
      take long.</p>
    '''
    html_body = _email_shell('Payment received', body_html)
    _send(subject, plain_text, html_body, submission.user.email)


def send_deposit_approved_email(submission):
    plan_name = submission.plan.name if submission.plan else 'your plan'
    credits = submission.plan.credits if submission.plan else 0
    subject = f'Payment approved — you\'re all set! ({settings.SITE_NAME})'
    plain_text = (
        f'Hi {submission.user.display_name},\n\n'
        f'Good news — your payment for "{plan_name}" has been approved.\n\n'
        f'{credits} credits have been added to your account, and your '
        f'dashboard is now fully unlocked.\n\n'
        f'Log in and head to AI Studio to start streaming.\n\n'
        f'— The {settings.SITE_NAME} Team'
    )
    body_html = f'''
      <p>Hi {submission.user.display_name},</p>
      <p>Good news — your payment for <strong>{plan_name}</strong> has been
      <strong style="color:#22c55e;">approved</strong>.</p>
      <p><strong>{credits} credits</strong> have been added to your account,
      and your dashboard is now fully unlocked.</p>
      <p>Head to AI Studio to start streaming with your own AI look.</p>
    '''
    html_body = _email_shell('Payment approved ✓', body_html)
    _send(subject, plain_text, html_body, submission.user.email)


def send_deposit_rejected_email(submission):
    plan_name = submission.plan.name if submission.plan else 'your plan'
    note = f'<p><strong>Reason:</strong> {submission.admin_note}</p>' if submission.admin_note else ''
    note_plain = f'\n\nReason: {submission.admin_note}' if submission.admin_note else ''
    subject = f'Payment could not be approved ({settings.SITE_NAME})'
    plain_text = (
        f'Hi {submission.user.display_name},\n\n'
        f'Unfortunately we were unable to approve your recent payment '
        f'submission for "{plan_name}" (${submission.amount}).{note_plain}\n\n'
        f'You\'re welcome to submit a new payment with a valid receipt at '
        f'any time.\n\n'
        f'— The {settings.SITE_NAME} Team'
    )
    body_html = f'''
      <p>Hi {submission.user.display_name},</p>
      <p>Unfortunately we were unable to approve your recent payment
      submission for <strong>{plan_name}</strong> (${submission.amount}).</p>
      {note}
      <p>You're welcome to submit a new payment with a valid receipt at
      any time from your account.</p>
    '''
    html_body = _email_shell('Payment not approved', body_html)
    _send(subject, plain_text, html_body, submission.user.email)
