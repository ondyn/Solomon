from django.urls import include, path
from utilities.urls import get_model_urls

from . import models, views


def changelog(model):
    return views.IssuesObjectChangeLogView.as_view(), {"model": model}


urlpatterns = [
    # Issue categories
    path(
        "categories/",
        views.IssueCategoryListView.as_view(),
        name="issuecategory_list",
    ),
    path(
        "categories/add/",
        views.IssueCategoryEditView.as_view(),
        name="issuecategory_add",
    ),
    path(
        "categories/<int:pk>/",
        views.IssueCategoryView.as_view(),
        name="issuecategory",
    ),
    path(
        "categories/<int:pk>/edit/",
        views.IssueCategoryEditView.as_view(),
        name="issuecategory_edit",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.IssueCategoryDeleteView.as_view(),
        name="issuecategory_delete",
    ),
    path(
        "categories/<int:pk>/changelog/",
        *changelog(models.IssueCategory),
        name="issuecategory_changelog",
    ),
    # Asset tags
    path("tags/", views.AssetTagListView.as_view(), name="assettag_list"),
    path("tags/add/", views.AssetTagEditView.as_view(), name="assettag_add"),
    path("tags/print/", views.AssetTagLabelView.as_view(), name="assettag_labels"),
    path("tags/<int:pk>/", views.AssetTagView.as_view(), name="assettag"),
    path("tags/<int:pk>/edit/", views.AssetTagEditView.as_view(), name="assettag_edit"),
    path(
        "tags/<int:pk>/delete/",
        views.AssetTagDeleteView.as_view(),
        name="assettag_delete",
    ),
    path("tags/<int:pk>/qr.svg", views.AssetTagQRView.as_view(), name="assettag_qr"),
    path(
        "tags/<int:pk>/changelog/",
        *changelog(models.AssetTag),
        name="assettag_changelog",
    ),
    path(
        "tags/<int:pk>/",
        include(get_model_urls("solomon_issues", "assettag")),
    ),
    # Issues
    path("issues/", views.IssueListView.as_view(), name="issue_list"),
    path("issues/add/", views.IssueEditView.as_view(), name="issue_add"),
    path("issues/<int:pk>/", views.IssueView.as_view(), name="issue"),
    path("issues/<int:pk>/edit/", views.IssueEditView.as_view(), name="issue_edit"),
    path(
        "issues/<int:pk>/delete/", views.IssueDeleteView.as_view(), name="issue_delete"
    ),
    path(
        "issues/<int:pk>/comment/",
        views.IssueCommentCreateView.as_view(),
        name="issue_comment",
    ),
    path(
        "issues/<int:pk>/status/",
        views.IssueStatusUpdateView.as_view(),
        name="issue_status",
    ),
    path(
        "issues/<int:pk>/changelog/",
        *changelog(models.Issue),
        name="issue_changelog",
    ),
    # Public endpoints reached from a printed QR code
    path("t/<str:code>/", views.PublicTagView.as_view(), name="public_tag"),
    path(
        "t/<str:code>/report/", views.PublicReportView.as_view(), name="public_report"
    ),
    path("r/<str:token>/", views.PublicIssueView.as_view(), name="public_issue"),
    path(
        "u/<str:token>/",
        views.PublicUnsubscribeView.as_view(),
        name="public_unsubscribe",
    ),
]
