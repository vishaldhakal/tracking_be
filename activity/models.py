from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
from pathlib import Path

class Website(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    site_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    tracking_code = models.TextField(blank=True, null=True)
    domain = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        super().save(*args, **kwargs)

    def generate_tracking_code(self):
        return f"""
        <script>
        function loadChatWidget(callback) {{
            const script = document.createElement('script');
            script.src = '{settings.SITE_URL}/{settings.STATIC_URL}js/chat-widget.js';
            script.onload = callback;
            document.head.appendChild(script);
        }}

        (function() {{
            const TRACKING_URL = '{settings.SITE_URL}/api/track/';
            const CHAT_URL = '{settings.SITE_URL}/api/chat/';
            const SITE_ID = '{self.site_id}';
            let pageStartTime = Date.now();
            let visitorId = localStorage.getItem('visitorId');
            let visitorEmail = localStorage.getItem('visitorEmail');
            let heartbeatInterval;

            function generateFingerprint() {{
                const screen = `${{window.screen.width}}x${{window.screen.height}}`;
                const colorDepth = window.screen.colorDepth;
                const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                const language = navigator.language;
                const platform = navigator.platform;
                const fingerprint = btoa(`${{screen}}-${{colorDepth}}-${{timezone}}-${{language}}-${{platform}}`);
                
                if (!localStorage.getItem('visitorId')) {{
                    localStorage.setItem('visitorId', fingerprint);
                    visitorId = fingerprint;
                }}
                return fingerprint;
            }}

            if (!visitorId) {{
                visitorId = generateFingerprint();
            }}

            function track(eventType, data) {{
                const commonData = {{
                    visitor_id: visitorId || generateFingerprint,
                    visitor_email: visitorEmail,
                    user_agent: navigator.userAgent,
                    language: navigator.language,
                    screen_resolution: `${{window.screen.width}}x${{window.screen.height}}`,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
                }};

                fetch(TRACKING_URL, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        site_id: SITE_ID,
                        event_type: eventType,
                        ...commonData,
                        ...data
                    }})
                }});
            }}

            function trackPageDuration(isHeartbeat = false) {{
                const duration = Math.round((Date.now() - pageStartTime) / 1000);
                track(isHeartbeat ? 'Heartbeat' : 'Viewed Page', {{
                    page_title: document.title,
                    page_url: window.location.href,
                    page_referrer: document.referrer || null,
                    page_duration: duration
                }});
            }}

            function startHeartbeat() {{
                heartbeatInterval = setInterval(() => {{
                    trackPageDuration(true);
                }}, 30000);
            }}

            function stopHeartbeat() {{
                if (heartbeatInterval) {{
                    clearInterval(heartbeatInterval);
                }}
            }}

            // Track initial page view
            track('Viewed Page', {{
                page_title: document.title,
                page_url: window.location.href,
                page_referrer: document.referrer || null
            }});
            startHeartbeat();

            // Load chat widget and initialize after it's loaded
            loadChatWidget(function() {{
                const chatWidget = new ChatWidget({{
                    TRACKING_URL,
                    CHAT_URL,
                    SITE_ID
                }});
            }});

            document.addEventListener('submit', function(e) {{
                const form = e.target;
                const formData = new FormData(form);
                const data = {{}};
                formData.forEach((value, key) => data[key] = value);
                
                if (data.email) {{
                    localStorage.setItem('visitorEmail', data.email);
                    localStorage.setItem('visitorId', btoa(data.email));
                    visitorEmail = data.email;
                    visitorId = btoa(data.email);
                }}
                
                track('Form Submission', {{
                    form_data: data,
                    form_id: form.id || 'unknown',
                    page_url: window.location.href,
                        page_referrer: document.referrer || null
                    }});
            }});

            // Handle page visibility
            document.addEventListener('visibilitychange', function() {{
                if (document.hidden) {{
                    trackPageDuration();
                    stopHeartbeat();
                }} else {{
                    pageStartTime = Date.now();
                    startHeartbeat();
                }}
            }});

            // Track page duration before user leaves
            window.addEventListener('beforeunload', () => {{
                trackPageDuration();
                stopHeartbeat();
            }});
        }})();
        </script>
        """

    def __str__(self):
        if not self.name and not self.domain:
            return f"Website {self.site_id}"
        return self.name or self.domain

    def delete(self, *args, **kwargs):
        # Delete related chats first
        self.chat_set.all().delete()
        # Delete related activities
        self.activity_set.all().delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Website"
        verbose_name_plural = "Websites"


class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class People(models.Model):
    STAGE_CHOICES = [
        ("Contact", "Contact"),
        ("Buyer", "Buyer"),
        ("Lead", "Lead"),
        ("Nurture", "Nurture"),
        ("Closed", "Closed"),
        ("Past Client", "Past Client"),
        ("Sphere", "Sphere"),
        ("Trash", "Trash"),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=100)
    last_activity = models.DateTimeField(blank=True, null=True)
    stage = models.CharField(
        max_length=100, blank=True, null=True, choices=STAGE_CHOICES
    )
    source = models.CharField(max_length=100, blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visitor_id = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=10, blank=True, null=True)
    screen_resolution = models.CharField(max_length=50, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["visitor_id"]),
            models.Index(fields=["email"]),
        ]


class Activity(models.Model):
    ACTIVITY_TYPE_CHOICES = [
        ("Viewed Page", "Viewed Page"),
        ("Form Submission", "Form Submission"),
        ("Heartbeat", "Heartbeat"),
        ("Inquiry", "Inquiry"),
    ]

    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    people = models.ForeignKey(People, on_delete=models.CASCADE, null=True, blank=True)
    activity_type = models.CharField(max_length=50)
    message = models.TextField(blank=True, null=True)
    page_title = models.CharField(max_length=255, blank=True, null=True)
    page_url = models.URLField(blank=True, null=True)
    page_referrer = models.URLField(blank=True, null=True, max_length=2000)
    page_duration = models.IntegerField(blank=True, null=True)
    form_data = models.JSONField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    occured_at = models.DateTimeField(auto_now_add=True)
    visitor_id = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=10, blank=True, null=True)
    screen_resolution = models.CharField(max_length=50, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)
    last_heartbeat = models.DateTimeField(auto_now=True)

    def __str__(self):
        website_name = self.website.name or self.website.domain if self.website else "Unknown Website"
        person_name = self.people.name if self.people else f"Anonymous ({self.visitor_id})"
        return f"{self.activity_type}: {person_name} on {website_name}"

    class Meta:
        ordering = ["-occured_at"]
        indexes = [
            models.Index(fields=["visitor_id"]),
            models.Index(fields=["occured_at"]),
        ]
        verbose_name_plural = "Activities"

    @property
    def is_online(self):
        if not self.last_heartbeat:
            return False
        return (timezone.now() - self.last_heartbeat).total_seconds() < 60

    @property
    def is_anonymous(self):
        return self.people is None


class Chat(models.Model):
    CHAT_STATUS = (
        ('active', 'Active'),
        ('closed', 'Closed'),
    )
    
    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    visitor_id = models.CharField(max_length=255)
    people = models.ForeignKey(People, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=CHAT_STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    unread_count = models.IntegerField(default=0)
    last_message = models.TextField(blank=True, null=True)

    def __str__(self):
        website_name = self.website.domain if self.website else "Unknown Website"
        person_name = self.people.name if self.people else f"Anonymous ({self.visitor_id})"
        return f"Chat with {person_name} on {website_name}"

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Chat"
        verbose_name_plural = "Chats"

    def update_last_message(self, message_text):
        self.last_message = message_text
        self.save(update_fields=['last_message', 'updated_at'])


class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    is_admin = models.BooleanField(default=False)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
