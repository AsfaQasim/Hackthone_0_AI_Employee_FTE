---
email_id: "19c574c3c98eac4a"
sender: "Google Cloud <CloudPlatform-noreply@google.com>"
sender_email: "CloudPlatform-noreply@google.com"
sender_name: "Google Cloud"
subject: "[Product Update] Automatic enablement of new OpenTelemetry ingestion API"
date: "Fri, 13 Feb 2026 05:58:59 -0800"
priority: "medium"
labels: ["UNREAD", "CATEGORY_UPDATES", "INBOX"]
processed_at: "2026-02-17T18:10:21.017366Z"
source: "gmail"
type: "email_task"
status: "pending"
---

# Email: [Product Update] Automatic enablement of new OpenTelemetry ingestion API

**From**: Google Cloud <CloudPlatform-noreply@google.com>  
**Date**: Fri, 13 Feb 2026 05:58:59 -0800  
**Priority**: 🟡 Medium  
**Labels**: UNREAD, CATEGORY_UPDATES, INBOX

## Email Content

We’re enabling a new OTLP ingestion API starting Mar 23, 2026.

|  |  |  ![](https://services.google.com/fh/files/emails/new_logo.png)  
---  
|  [MY
CONSOLE](https://c.gle/AEJ26qvcVPj5XZyZhf1Fu8nBMRbMcYtehFs4qFR7Ge9czvMV6FiMfMVAMuluSrSPEsKc8TfaW_1E4b-WOjRdIxhkOWVi8f_XbSN6QzApne0lS2NASTVkPPPhTOUv7nF7syk)  
---  
|  |  Hello Asfa, _You may have previously received a notification regarding this update. If so, please disregard this message._ We’re writing to let you know that **Cloud Observability** has launched a new [**OpenTelemetry (OTel)** ingestion API](https://c.gle/AEJ26qtNnRyh6JRfZlIRGBItAlKNraxFnY-EgmugZPkPvjyeO-6FZaQsI7qwiZ6gYyPeWGIXnbQuF4nczn08cUT2WuXtwOUp-HPH3kN42ht_XwpFSPjJeTJy6xTOfcYbqGXJPXtEAgGh9tWa0VGUboMR3hYTDOkZqgwHnYgz0hkb0n0rtppkauDNe1k) that supports native **OpenTelemetry Protocol (OTLP)** logs, trace spans, and metrics. Starting **March 23, 2026** , this API will be added as a dependency for the current **Cloud Logging** , **Cloud Trace** , and **Cloud Monitoring** ingestion APIs. This change ensures a seamless transition as collection tools migrate to this new unified endpoint.

### What you need to know

**Key changes:**

  * The existing Cloud Observability ingestion APIs (`logging.googleapis.com`, `cloudtrace.googleapis.com`, and `monitoring.googleapis.com`) are automatically activated when you create a Google Cloud project using the **Google Cloud console** or `gcloud` CLI. The behavior remains unchanged for projects created via API, which do not have these ingestion APIs enabled by default. Starting **March 23, 2026** , the new OTel ingestion endpoint `telemetry.googleapis.com` will automatically activate when any of these specified APIs are enabled.
  * In addition, we will automatically enable this new endpoint for all existing projects that already have current ingestion APIs active.

### What you need to do

No action is required from you for this API enablement change, and there will
be no disruption to your existing services. You may disable the API at any
time by following these
[instructions](https://c.gle/AEJ26quIl8gKXseaH5Zej5PZacWMYwa8YxGSpSxFC92426dBjbv7b0Yo5ZrFDokCIpnHQTK5njqki6h84pVEXnqeVNVJtyOSAuLHQUn1UXfbohEOwVu0787cCUv9oEUu96u7ct-_54TzWlmC_vQTy7NApnstxDeugBvSG-
OCvdw). Refer to the attachment for a list of the projects that will
automatically enable the new endpoint.

### We’re here to help

If you have any questions or require assistance, please contact [Google Cloud
Support](https://c.gle/AEJ26qvxMGwNONBazzUpXbMJ9RdmBxh5GPxsDz0rfSjS2fFyiw7xstFPVLuh8NY1Teqm4INhjcT-
GwrSS3ITvNC0v5Y_2BwiFSXkDVWwhwlUFyn0wNDXKBXo7YI). Thanks for choosing Google
Cloud Observability.  
---  
| – The Google Cloud Team  
---  
|  |  |   
---|---  
![](http://services.google.com/fh/files/emails/gcp_free_trail_forum_new.png) |  [SUPPORT](https://c.gle/AEJ26qvxMGwNONBazzUpXbMJ9RdmBxh5GPxsDz0rfSjS2fFyiw7xstFPVLuh8NY1Teqm4INhjcT-GwrSS3ITvNC0v5Y_2BwiFSXkDVWwhwlUFyn0wNDXKBXo7YI)  
---|---  
|
![](http://services.google.com/fh/files/emails/gcp_newsletter_email_cloud_footer_logo.png)  
---  
  
**Was this information helpful?**  
  
[![Yes](https://services.google.com/fh/files/emails/happy_emojis.png)](https://c.gle/AEJ26qtdNfaqt16VArqa4dCbiHx0ZOeHQ8bjLix_E1Z0knpZ3JVw0oBh2ijF8uqpX5MvMJwQS0A3jnT1og3mMiSImf3Yd3NLLZwgOqs-
vHAD_Nwr4flgMoBMbpr-bolF8EEU61TtXPIoFKN3Ob-
et7M2EuLl5fyUWpf9fYtONZFql8eSQhtU7imiXpm-mA5fVln625OqOrxH6aGqx-
oz9U09lVgcRc1Q5-1yRrD-36IuCu0qx3IhRBT7iS4ClmuhwDpUhg)
[![Neutral](https://services.google.com/fh/files/emails/neutral_emojis.png)](https://c.gle/AEJ26qu15fTygulmPwh5O5kJ9581omOgXDxCATqaqTEPpIyyElZFHesWBxcnkBO07I1ED_44gHKCGTbjSqYCgh6Z5HbO1lthz5D48ROPrX-
CN5VAW0e0TBeIx8yadzxtAoCecnOOBK3uqbfAQmjTZcI3DCnEYkL56Dae7RW5fiaSu5mL02MMZX-
MIQyriy-
nqFY_fKDKLeytsi5nJF0s3pqW6cxLdZkXUY-Z0Y-iycBmKJ5ICFsJQFA3bpUXLmsK3OuwAwgdF6s)
[![No](https://services.google.com/fh/files/emails/sad_emojis.png)](https://c.gle/AEJ26qv0RAti9CuM3wi-
Zm987YLpFlOJCSX31m2UNiRg4dk8Sz-
ZEnkId58dMGe1KTz_QvY_5QZntesTQArOiKok2bQlCKtGAelZUyTafaX_kIUSA10pa5INPSukpwOsrOvevXcD1YnOu6-Pht3sjmPZqi51NrIxdUXz3Z7GC8uDd_4GaIJr3A_V_MPDZlMe39c2umk-
tos3jVcS7NKcTJBn8SEgTuxE9DR3VXcwEdRscoD2vJ9_m5D49jV4WLIZ9a19)  
  
© 2026 Google LLC 1600 Amphitheatre Parkway, Mountain View, CA 94043  
  
You’ve received this mandatory service announcement to update you about
important changes to Google Cloud or your account.  
| [![Visit Google Cloud blog](http://services.google.com/fh/files/emails/gcp_newsletter_email_blogger.png)](https://c.gle/AEJ26qtrmCthXkAxs0wzs45TJ9Jmav7UQJt-IuDznQlTqASMnoGA9Ap1-l5-nY7_y26XQPxalmKg1ObPngYBYklyVPLc5JZlFod6_8aLV4ADIFvfruDJ2PvgigF0GUiD0TNkGEI) |  | [![Visit GCP on GitHub](https://services.google.com/fh/files/emails/gcp_newsletter_email_github.png)](https://c.gle/AEJ26qujz19i9Hui3HvlQVWzRwc_bM_Y-8LEfpDJiybCkQw6DwtKs4S-CEo389ovl4b5BZjxq3yrtG6W52DOs69K8E9HGLBgsbPgnIXCw_IsRVZ4KiqZKEWivef-31Mlb1ODwab_GvL2WnL4b9GE) |  | [![Visit Google Cloud on LinkedIn](http://services.google.com/fh/files/emails/gcp_newsletter_email_linkedin.png)](https://c.gle/AEJ26qtpHdgWo_W5G5C5PZRoT8i6LixNcC1c7qgf5eODdKxY6kGa13XoaWLk6R8Rf5MbeUrzaOLyz-5SwnZnE-2bmXGn8rGuMMoMjxy5F6aX-ved29IuTKdICsH2Z9dWt2Py2iyisB7_UH8hIxMIDOSM3fc) |  | [![Visit Google Cloud on Twitter](http://services.google.com/fh/files/emails/gcp_newsletter_email_twitter.png)](https://c.gle/AEJ26qu-wM-TWEsdOmFrrjsUPe294CCcc7E_n8uyzFevT5ENdaT0R1E9_6o-hn4KKHJiNEKeJDrk0cxnH7LclV1WryF2_cgMk7pVffnbUUBbjfITtqvzEQz9dLyFosE7KcLCdmKzmgY4)  
---|---|---|---|---|---|---  
  
![](https://notifications.google.com/g/img/AEJ26qus9VKk74r7ZpixpX68yEayGoVYzJTENKXcqz3JQDNs_0EwZJ8q7Y1I0mep7ldwItf9dO8861hSABxtZEHNsHKXtdBkd9HajbiM532fnDSePUOU-p8KK6oADInrAL0ipQT4mg.gif)

---

## Action Items

- [ ] Review and respond to this email

## Links

- [View in Gmail](https://mail.google.com/mail/u/0/#inbox/19c574c3c98eac4a)

---

*Processed by Gmail Watcher Skill v1.0.0*
