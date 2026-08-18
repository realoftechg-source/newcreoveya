from django.shortcuts import render


PLANS = [
    {
        'key': 'free',
        'name': 'Free',
        'price': 0,
        'period': 'forever',
        'credits': 50,
        'features': [
            '50 credits / month',
            '720p max resolution',
            '1 AI character',
            'Watermarked streams',
            'Community support',
        ],
        'highlight': False,
    },
    {
        'key': 'starter',
        'name': 'Starter',
        'price': 19,
        'period': 'month',
        'credits': 500,
        'features': [
            '500 credits / month',
            '1080p resolution',
            '5 AI characters',
            'No watermark',
            'Email support',
        ],
        'highlight': False,
    },
    {
        'key': 'professional',
        'name': 'Professional',
        'price': 49,
        'period': 'month',
        'credits': 2500,
        'features': [
            '2,500 credits / month',
            '4K resolution',
            'Unlimited AI characters',
            'Custom backgrounds',
            'Priority support',
            'Advanced analytics',
        ],
        'highlight': True,
    },
    {
        'key': 'enterprise',
        'name': 'Enterprise',
        'price': 199,
        'period': 'month',
        'credits': 10000,
        'features': [
            '10,000 credits / month',
            '4K+ resolution',
            'Dedicated infrastructure',
            'Custom AI integration',
            'SLA & 24/7 support',
            'Team seats',
        ],
        'highlight': False,
    },
]

FAQS = [
    {
        'q': 'What is AI Live Studio?',
        'a': 'AI Live Studio is a platform for running AI-enhanced live '
             'streams — swap avatars, backgrounds and voices in real time, '
             'then broadcast anywhere.',
    },
    {
        'q': 'Do I need my own AI model?',
        'a': 'The platform ships with modular placeholders for stream '
             'processing so you can plug in your own AI API or model '
             'provider without touching the rest of the app.',
    },
    {
        'q': 'How do credits work?',
        'a': 'Every plan includes a monthly credit allowance. Credits are '
             'consumed while a stream is live and can be topped up anytime '
             'from the Credits page.',
    },
    {
        'q': 'Can I cancel anytime?',
        'a': 'Yes. You can downgrade to the Free plan at any time from '
             'Billing — no long-term contracts.',
    },
    {
        'q': 'Is my data secure?',
        'a': 'All traffic is served over HTTPS, passwords are hashed with '
             'Django\u2019s PBKDF2 algorithm, and sessions use secure, '
             'HTTP-only cookies.',
    },
]

TESTIMONIALS = [
    {
        'name': 'Amara Chen',
        'role': 'Content Creator',
        'quote': 'Switched my whole streaming setup over in an afternoon. '
                  'The AI Studio interface feels like a real product.',
    },
    {
        'name': 'David Okafor',
        'role': 'Founder, Loopline Media',
        'quote': 'The credits and analytics system gave us exactly the '
                  'visibility we needed to price our own service.',
    },
    {
        'name': 'Priya Natarajan',
        'role': 'Livestream Producer',
        'quote': 'Clean dashboard, fast camera preview, and the plan '
                  'system just works out of the box.',
    },
]


def landing_view(request):
    from django.conf import settings
    from payments.models import CreditPlan
    context = {
        'plans': CreditPlan.objects.filter(is_active=True),
        'faqs': FAQS,
        'testimonials': TESTIMONIALS,
        'windows_app_download_url': settings.WINDOWS_APP_DOWNLOAD_URL,
    }
    return render(request, 'landing/landing.html', context)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)
