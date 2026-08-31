"""Staff and public views for Solomon Issues."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.views import View
from netbox.views import generic
from netbox.views.generic import ObjectChangeLogView
from utilities.views import ViewTab, register_model_view

from . import filtersets, forms, models, notifications, tables
from .choices import (
    AssetTagStatusChoices,
    IssueEventTypeChoices,
    IssueSourceChoices,
    IssueStatusChoices,
    PublicIssueVisibilityChoices,
    VisibilityChoices,
)
from .qr import build_qr_svg
from .utils import anonymous_write, client_ip, get_setting, public_languages


class IssuesObjectChangeLogView(ObjectChangeLogView):
    base_template = "generic/object.html"


#
# Issue categories
#


class IssueCategoryListView(generic.ObjectListView):
    queryset = models.IssueCategory.objects.annotate(issue_count=Count("issues"))
    table = tables.IssueCategoryTable
    filterset = filtersets.IssueCategoryFilterSet


class IssueCategoryView(generic.ObjectView):
    queryset = models.IssueCategory.objects.all()
    template_name = "solomon_issues/issuecategory.html"

    def get_extra_context(self, request, instance):
        return {
            "open_issues": instance.issues.filter(
                status__in=IssueStatusChoices.OPEN_STATUSES
            ).count(),
            "total_issues": instance.issues.count(),
        }


class IssueCategoryEditView(generic.ObjectEditView):
    queryset = models.IssueCategory.objects.all()
    form = forms.IssueCategoryForm


class IssueCategoryDeleteView(generic.ObjectDeleteView):
    queryset = models.IssueCategory.objects.all()


#
# Asset tags
#


class AssetTagListView(generic.ObjectListView):
    queryset = models.AssetTag.objects.select_related("category").annotate(
        open_issue_count=Count(
            "issues",
            filter=Q(issues__status__in=IssueStatusChoices.OPEN_STATUSES),
        )
    )
    table = tables.AssetTagTable
    filterset = filtersets.AssetTagFilterSet


class AssetTagView(generic.ObjectView):
    queryset = models.AssetTag.objects.select_related("category", "assigned_group")
    template_name = "solomon_issues/assettag.html"

    def get_extra_context(self, request, instance):
        return {
            "public_url": instance.public_url(request),
            "open_issues": instance.open_issues().order_by("-created"),
            "recent_issues": instance.issues.order_by("-created")[:20],
        }


class AssetTagEditView(generic.ObjectEditView):
    queryset = models.AssetTag.objects.all()
    form = forms.AssetTagForm


class AssetTagDeleteView(generic.ObjectDeleteView):
    queryset = models.AssetTag.objects.all()


class AssetTagQRView(PermissionRequiredMixin, View):
    """Return the QR code for one asset tag as a standalone SVG."""

    permission_required = "solomon_issues.view_assettag"

    def get(self, request, pk):
        tag = get_object_or_404(models.AssetTag, pk=pk)
        svg = build_qr_svg(
            tag.public_url(request),
            error_correction=get_setting("qr_error_correction", "M"),
        )
        response = HttpResponse(svg, content_type="image/svg+xml")
        response["Content-Disposition"] = f'inline; filename="qr-{tag.code}.svg"'
        return response


class AssetTagLabelView(PermissionRequiredMixin, View):
    """Printable label sheet for one or more asset tags."""

    permission_required = "solomon_issues.print_assettag"

    def get(self, request):
        pks = request.GET.getlist("pk")
        queryset = models.AssetTag.objects.select_related("category")
        tags = (
            queryset.filter(pk__in=pks)
            if pks
            else queryset.filter(status=AssetTagStatusChoices.STATUS_ACTIVE)
        )
        labels = [
            {
                "tag": tag,
                "url": tag.public_url(request),
                "svg": build_qr_svg(
                    tag.public_url(request),
                    error_correction=get_setting("qr_error_correction", "M"),
                    box_size=8,
                    border=1,
                ),
            }
            for tag in tags
        ]
        return render(
            request,
            "solomon_issues/assettag_labels.html",
            {"labels": labels, "count": len(labels)},
        )

    def post(self, request):
        pks = request.POST.getlist("pk")
        if pks:
            models.AssetTag.objects.filter(pk__in=pks).update(printed_at=timezone.now())
            messages.success(
                request, _("Marked %(count)s labels as printed.") % {"count": len(pks)}
            )
        return redirect("plugins:solomon_issues:assettag_list")


#
# Issues
#


class IssueListView(generic.ObjectListView):
    queryset = models.Issue.objects.select_related(
        "asset_tag", "category", "assigned_to", "assigned_group"
    )
    table = tables.IssueTable
    filterset = filtersets.IssueFilterSet


class IssueView(generic.ObjectView):
    queryset = models.Issue.objects.select_related(
        "asset_tag", "category", "assigned_to", "assigned_group", "reporter_user"
    )
    template_name = "solomon_issues/issue.html"

    def get_extra_context(self, request, instance):
        can_see_internal = request.user.has_perm("solomon_issues.view_internal_issue")
        events = instance.events.select_related("user")
        comments = instance.comments.select_related("author")
        if not can_see_internal:
            events = events.filter(visibility=VisibilityChoices.VISIBILITY_PUBLIC)
            comments = comments.filter(visibility=VisibilityChoices.VISIBILITY_PUBLIC)
        return {
            "timeline": events,
            "comments": comments,
            "attachments": instance.attachments.all(),
            "subscribers": instance.subscribers.filter(is_active=True),
            "notifications": instance.notifications.all()[:25],
            "comment_form": forms.IssueCommentForm(),
            "status_form": forms.IssueStatusForm(
                initial={
                    "status": instance.status,
                    "priority": instance.priority,
                    "assigned_to": instance.assigned_to_id,
                }
            ),
            "public_url": instance.public_url(request),
            "can_manage": request.user.has_perm("solomon_issues.manage_issue"),
        }


class IssueEditView(generic.ObjectEditView):
    queryset = models.Issue.objects.all()
    form = forms.IssueForm

    def alter_object(self, obj, request, url_args, url_kwargs):
        if obj.pk is None:
            obj.source = obj.source or IssueSourceChoices.SOURCE_STAFF
            obj.reporter_user = obj.reporter_user or request.user
        return obj


class IssueDeleteView(generic.ObjectDeleteView):
    queryset = models.Issue.objects.all()


class IssueCommentCreateView(PermissionRequiredMixin, View):
    permission_required = "solomon_issues.add_issuecomment"

    def post(self, request, pk):
        issue = get_object_or_404(models.Issue, pk=pk)
        form = forms.IssueCommentForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("The reply could not be saved."))
            return redirect(issue.get_absolute_url())

        comment = form.save(commit=False)
        comment.issue = issue
        comment.author = request.user
        comment.save()

        issue.log_event(
            IssueEventTypeChoices.EVENT_COMMENT,
            message=comment.body,
            user=request.user,
            visibility=comment.visibility,
        )
        if comment.visibility == VisibilityChoices.VISIBILITY_PUBLIC:
            notifications.notify(
                issue,
                IssueEventTypeChoices.EVENT_COMMENT,
                message=comment.body,
                request=request,
                comment=comment,
            )
        messages.success(request, _("Reply added."))
        return redirect(issue.get_absolute_url())


class IssueStatusUpdateView(PermissionRequiredMixin, View):
    permission_required = "solomon_issues.manage_issue"

    def post(self, request, pk):
        issue = get_object_or_404(models.Issue, pk=pk)
        form = forms.IssueStatusForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("The status update could not be saved."))
            return redirect(issue.get_absolute_url())

        data = form.cleaned_data
        changed = False

        if data.get("priority") and data["priority"] != issue.priority:
            previous = issue.priority
            issue.priority = data["priority"]
            issue.save()
            issue.log_event(
                IssueEventTypeChoices.EVENT_PRIORITY_CHANGED,
                user=request.user,
                data={"from": previous, "to": issue.priority},
            )
            changed = True

        if data.get("assigned_to") != issue.assigned_to:
            issue.assigned_to = data.get("assigned_to")
            issue.save()
            issue.log_event(
                IssueEventTypeChoices.EVENT_ASSIGNED,
                user=request.user,
                visibility=VisibilityChoices.VISIBILITY_INTERNAL,
                data={"to": issue.assigned_to.username if issue.assigned_to else None},
            )
            changed = True

        note = data.get("resolution", "")
        if note and note != issue.resolution:
            issue.resolution = note
            issue.save()

        event = issue.apply_status(data["status"], user=request.user, note=note)
        changed = changed or event is not None

        if changed and data.get("notify"):
            notifications.notify(
                issue,
                event.event_type if event else IssueEventTypeChoices.EVENT_UPDATED,
                message=note,
                request=request,
            )
        messages.success(request, _("Issue updated."))
        return redirect(issue.get_absolute_url())


#
# Public (unauthenticated) views
#


def _public_tag_or_404(code):
    tag = models.AssetTag.objects.select_related("category").filter(code=code).first()
    if tag is None or tag.status == AssetTagStatusChoices.STATUS_RETIRED:
        raise Http404
    return tag


def _visible_issues(tag):
    visibility = get_setting(
        "public_issue_visibility", PublicIssueVisibilityChoices.VISIBILITY_OPEN
    )
    if (
        not tag.show_open_issues
        or visibility == PublicIssueVisibilityChoices.VISIBILITY_NONE
    ):
        return models.Issue.objects.none()
    queryset = tag.issues.filter(is_public=True)
    if visibility == PublicIssueVisibilityChoices.VISIBILITY_OPEN:
        queryset = queryset.filter(status__in=IssueStatusChoices.OPEN_STATUSES)
    return queryset.order_by("-created")[:25]


def _reports_allowed(tag, request=None):
    """Anonymous reporting is opt-in; `report_issue` holders can always report."""
    if tag.status != AssetTagStatusChoices.STATUS_ACTIVE:
        return False
    if (
        request is not None
        and request.user.is_authenticated
        and request.user.has_perm("solomon_issues.report_issue")
    ):
        return True
    return get_setting("allow_anonymous_reports", True) and tag.allow_public_reports


def _rate_limited(request):
    limit = int(get_setting("rate_limit_reports_per_hour", 10) or 0)
    if limit <= 0:
        return False
    key = f"solomon_issues:report:{client_ip(request)}"
    count = cache.get(key, 0)
    if count >= limit:
        return True
    cache.set(key, count + 1, 3600)
    return False


class PublicLanguageMixin:
    """Honour ?lang= on public pages and remember the choice in a cookie."""

    def dispatch(self, request, *args, **kwargs):
        requested = request.GET.get("lang")
        available = public_languages()
        if requested not in available:
            return super().dispatch(request, *args, **kwargs)

        translation.activate(requested)
        request.LANGUAGE_CODE = requested
        response = super().dispatch(request, *args, **kwargs)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            requested,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=request.is_secure(),
            samesite="Lax",
        )
        return response

    def language_context(self, request):
        current = translation.get_language()
        return {
            "language_options": [
                {
                    "code": code,
                    "name": label,
                    "active": current == code,
                    "url": f"{request.path}?lang={code}",
                }
                for code, label in public_languages().items()
            ]
        }


class PublicTagView(PublicLanguageMixin, View):
    """Landing page reached by scanning an asset tag QR code."""

    def get(self, request, code):
        tag = _public_tag_or_404(code)
        return render(
            request,
            "solomon_issues/public/tag.html",
            {
                "tag": tag,
                "issues": _visible_issues(tag),
                "can_report": _reports_allowed(tag, request),
                "form": forms.PublicIssueReportForm(asset_tag=tag),
                **self.language_context(request),
            },
        )


class PublicReportView(PublicLanguageMixin, View):
    """Accept a problem report submitted from the public tag page."""

    def get(self, request, code):
        return redirect("plugins:solomon_issues:public_tag", code=code)

    def post(self, request, code):
        tag = _public_tag_or_404(code)
        if not _reports_allowed(tag, request):
            raise Http404

        form = forms.PublicIssueReportForm(request.POST, request.FILES, asset_tag=tag)
        if not form.is_valid():
            return render(
                request,
                "solomon_issues/public/tag.html",
                {
                    "tag": tag,
                    "issues": _visible_issues(tag),
                    "can_report": True,
                    "form": form,
                    **self.language_context(request),
                },
                status=400,
            )

        if _rate_limited(request):
            return render(
                request,
                "solomon_issues/public/rate_limited.html",
                {"tag": tag},
                status=429,
            )

        data = form.cleaned_data
        user = request.user if request.user.is_authenticated else None
        with anonymous_write(request):
            issue = models.Issue.objects.create(
                asset_tag=tag,
                category=data.get("category") or tag.category,
                title=data["title"],
                description=data["description"],
                priority=data["priority"],
                source=(
                    IssueSourceChoices.SOURCE_PORTAL
                    if user
                    else IssueSourceChoices.SOURCE_QR
                ),
                reporter_user=user,
                reporter_name=data.get("reporter_name", ""),
                reporter_email=data.get("reporter_email", ""),
                reporter_phone=data.get("reporter_phone", ""),
                assigned_group=tag.assigned_group,
            )

            upload = data.get("attachment")
            if upload:
                attachment = models.IssueAttachment.objects.create(
                    issue=issue,
                    file=upload,
                    uploaded_by=user,
                    uploader_name=data.get("reporter_name", ""),
                )
                issue.log_event(
                    IssueEventTypeChoices.EVENT_ATTACHMENT,
                    message=attachment.file.name,
                    actor_name=issue.reporter_display,
                )

        notifications.notify(
            issue, IssueEventTypeChoices.EVENT_CREATED, request=request
        )
        return redirect("plugins:solomon_issues:public_issue", token=issue.access_token)


class PublicIssueView(PublicLanguageMixin, View):
    """Tokenised page letting a reporter follow their own report."""

    def get_issue(self, token):
        return get_object_or_404(
            models.Issue.objects.select_related("asset_tag", "category"),
            access_token=token,
        )

    def get(self, request, token, form=None):
        issue = self.get_issue(token)
        return render(
            request,
            "solomon_issues/public/issue.html",
            {
                "issue": issue,
                "timeline": issue.public_events().select_related("user"),
                "comments": issue.public_comments().select_related("author"),
                "attachments": issue.attachments.filter(is_public=True),
                "form": form or forms.PublicIssueReplyForm(),
                **self.language_context(request),
            },
        )

    def post(self, request, token):
        issue = self.get_issue(token)
        form = forms.PublicIssueReplyForm(request.POST)
        if not form.is_valid():
            return self.get(request, token, form=form)
        if _rate_limited(request):
            return render(
                request,
                "solomon_issues/public/rate_limited.html",
                {"tag": issue.asset_tag},
                status=429,
            )

        with anonymous_write(request):
            comment = models.IssueComment.objects.create(
                **form.as_comment_kwargs(issue)
            )
            issue.log_event(
                IssueEventTypeChoices.EVENT_COMMENT,
                message=comment.body,
                actor_name=issue.reporter_display,
            )
        notifications.notify(
            issue,
            IssueEventTypeChoices.EVENT_COMMENT,
            message=comment.body,
            request=request,
            comment=comment,
        )
        return redirect("plugins:solomon_issues:public_issue", token=token)


class PublicUnsubscribeView(View):
    def get(self, request, token):
        subscriber = get_object_or_404(models.IssueSubscriber, token=token)
        subscriber.is_active = False
        subscriber.save()
        return render(
            request,
            "solomon_issues/public/unsubscribed.html",
            {"subscriber": subscriber},
        )


#
# Cross-plugin tabs
#


@register_model_view(models.AssetTag, "issues")
class AssetTagIssuesView(generic.ObjectChildrenView):
    queryset = models.AssetTag.objects.all()
    child_model = models.Issue
    table = tables.IssueTable
    filterset = filtersets.IssueFilterSet
    template_name = "generic/object_children.html"
    tab = ViewTab(
        label=_("Issues"),
        badge=lambda obj: obj.issues.count(),
        permission="solomon_issues.view_issue",
    )

    def get_children(self, request, parent):
        return parent.issues.select_related("category", "assigned_to")
