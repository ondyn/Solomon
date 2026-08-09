from django.urls import path

from . import models, views


def changelog(model):
    return views.FacilitiesObjectChangeLogView.as_view(), {"model": model}


urlpatterns = [
    path("levels/", views.BuildingLevelListView.as_view(), name="level_list"),
    path("levels/add/", views.BuildingLevelEditView.as_view(), name="level_add"),
    path(
        "levels/<int:pk>/edit/",
        views.BuildingLevelEditView.as_view(),
        name="level_edit",
    ),
    path(
        "levels/<int:pk>/delete/",
        views.BuildingLevelDeleteView.as_view(),
        name="level_delete",
    ),
    path("levels/", views.BuildingLevelListView.as_view(), name="buildinglevel_list"),
    path(
        "levels/add/", views.BuildingLevelEditView.as_view(), name="buildinglevel_add"
    ),
    path(
        "levels/<int:pk>/edit/",
        views.BuildingLevelEditView.as_view(),
        name="buildinglevel_edit",
    ),
    path(
        "levels/<int:pk>/delete/",
        views.BuildingLevelDeleteView.as_view(),
        name="buildinglevel_delete",
    ),
    path(
        "levels/<int:pk>/changelog/",
        *changelog(models.BuildingLevel),
        name="buildinglevel_changelog",
    ),
    path("floor-plans/", views.FloorPlanListView.as_view(), name="floorplan_list"),
    path("floor-plans/add/", views.FloorPlanEditView.as_view(), name="floorplan_add"),
    path("floor-plans/<int:pk>/", views.FloorPlanView.as_view(), name="floorplan"),
    path(
        "floor-plans/<int:pk>/edit/",
        views.FloorPlanEditView.as_view(),
        name="floorplan_edit",
    ),
    path(
        "floor-plans/<int:pk>/delete/",
        views.FloorPlanDeleteView.as_view(),
        name="floorplan_delete",
    ),
    path(
        "floor-plans/<int:pk>/draw/",
        views.FloorPlanEditorView.as_view(),
        name="floorplan_draw",
    ),
    path(
        "floor-plans/<int:pk>/data/",
        views.FloorPlanDataView.as_view(),
        name="floorplan_data",
    ),
    path(
        "floor-plans/<int:pk>/publish/",
        views.FloorPlanPublishView.as_view(),
        name="floorplan_publish",
    ),
    path(
        "floor-plans/<int:pk>/changelog/",
        *changelog(models.FloorPlan),
        name="floorplan_changelog",
    ),
    path(
        "plan-revisions/<int:pk>/edit/",
        views.PlanRevisionEditView.as_view(),
        name="planrevision_edit",
    ),
    path("spaces/", views.SpaceListView.as_view(), name="space_list"),
    path("spaces/add/", views.SpaceEditView.as_view(), name="space_add"),
    path("spaces/<int:pk>/", views.SpaceView.as_view(), name="space"),
    path("spaces/<int:pk>/edit/", views.SpaceEditView.as_view(), name="space_edit"),
    path(
        "spaces/<int:pk>/delete/", views.SpaceDeleteView.as_view(), name="space_delete"
    ),
    path(
        "spaces/<int:pk>/changelog/", *changelog(models.Space), name="space_changelog"
    ),
    path(
        "space-assignments/",
        views.SpaceFlatAssignmentListView.as_view(),
        name="spaceflatassignment_list",
    ),
    path(
        "space-assignments/add/",
        views.SpaceFlatAssignmentEditView.as_view(),
        name="spaceflatassignment_add",
    ),
    path(
        "space-assignments/<int:pk>/edit/",
        views.SpaceFlatAssignmentEditView.as_view(),
        name="spaceflatassignment_edit",
    ),
    path(
        "space-assignments/<int:pk>/delete/",
        views.SpaceFlatAssignmentDeleteView.as_view(),
        name="spaceflatassignment_delete",
    ),
    path(
        "space-assignments/<int:pk>/changelog/",
        *changelog(models.SpaceFlatAssignment),
        name="spaceflatassignment_changelog",
    ),
    path("space-usages/", views.SpaceUsageListView.as_view(), name="spaceusage_list"),
    path(
        "space-usages/add/", views.SpaceUsageEditView.as_view(), name="spaceusage_add"
    ),
    path(
        "space-usages/<int:pk>/edit/",
        views.SpaceUsageEditView.as_view(),
        name="spaceusage_edit",
    ),
    path(
        "space-usages/<int:pk>/delete/",
        views.SpaceUsageDeleteView.as_view(),
        name="spaceusage_delete",
    ),
    path(
        "space-usages/<int:pk>/changelog/",
        *changelog(models.SpaceUsage),
        name="spaceusage_changelog",
    ),
    path("doors/", views.DoorListView.as_view(), name="door_list"),
    path("doors/add/", views.DoorEditView.as_view(), name="door_add"),
    path("doors/<int:pk>/", views.DoorView.as_view(), name="door"),
    path("doors/<int:pk>/edit/", views.DoorEditView.as_view(), name="door_edit"),
    path("doors/<int:pk>/delete/", views.DoorDeleteView.as_view(), name="door_delete"),
    path("doors/<int:pk>/changelog/", *changelog(models.Door), name="door_changelog"),
    path("locks/", views.LockCylinderListView.as_view(), name="lockcylinder_list"),
    path("locks/add/", views.LockCylinderEditView.as_view(), name="lockcylinder_add"),
    path(
        "locks/<int:pk>/edit/",
        views.LockCylinderEditView.as_view(),
        name="lockcylinder_edit",
    ),
    path(
        "locks/<int:pk>/delete/",
        views.LockCylinderDeleteView.as_view(),
        name="lockcylinder_delete",
    ),
    path(
        "locks/<int:pk>/changelog/",
        *changelog(models.LockCylinder),
        name="lockcylinder_changelog",
    ),
    path("key-profiles/", views.KeyProfileListView.as_view(), name="keyprofile_list"),
    path(
        "key-profiles/add/", views.KeyProfileEditView.as_view(), name="keyprofile_add"
    ),
    path("key-profiles/<int:pk>/", views.KeyProfileView.as_view(), name="keyprofile"),
    path(
        "key-profiles/<int:pk>/edit/",
        views.KeyProfileEditView.as_view(),
        name="keyprofile_edit",
    ),
    path(
        "key-profiles/<int:pk>/delete/",
        views.KeyProfileDeleteView.as_view(),
        name="keyprofile_delete",
    ),
    path(
        "key-profiles/<int:pk>/changelog/",
        *changelog(models.KeyProfile),
        name="keyprofile_changelog",
    ),
    path("keys/", views.KeyCopyListView.as_view(), name="keycopy_list"),
    path("keys/add/", views.KeyCopyEditView.as_view(), name="keycopy_add"),
    path("keys/<int:pk>/", views.KeyCopyView.as_view(), name="keycopy"),
    path("keys/<int:pk>/edit/", views.KeyCopyEditView.as_view(), name="keycopy_edit"),
    path(
        "keys/<int:pk>/delete/",
        views.KeyCopyDeleteView.as_view(),
        name="keycopy_delete",
    ),
    path(
        "keys/<int:pk>/changelog/", *changelog(models.KeyCopy), name="keycopy_changelog"
    ),
    path("key-issues/", views.KeyIssueListView.as_view(), name="keyissue_list"),
    path("key-issues/add/", views.KeyIssueEditView.as_view(), name="keyissue_add"),
    path(
        "key-issues/<int:pk>/edit/",
        views.KeyIssueEditView.as_view(),
        name="keyissue_edit",
    ),
    path(
        "key-issues/<int:pk>/delete/",
        views.KeyIssueDeleteView.as_view(),
        name="keyissue_delete",
    ),
    path(
        "key-issues/<int:pk>/changelog/",
        *changelog(models.KeyIssue),
        name="keyissue_changelog",
    ),
    path(
        "technical-systems/",
        views.TechnicalSystemListView.as_view(),
        name="technicalsystem_list",
    ),
    path(
        "technical-systems/add/",
        views.TechnicalSystemEditView.as_view(),
        name="technicalsystem_add",
    ),
    path(
        "technical-systems/<int:pk>/",
        views.TechnicalSystemView.as_view(),
        name="technicalsystem",
    ),
    path(
        "technical-systems/<int:pk>/edit/",
        views.TechnicalSystemEditView.as_view(),
        name="technicalsystem_edit",
    ),
    path(
        "technical-systems/<int:pk>/delete/",
        views.TechnicalSystemDeleteView.as_view(),
        name="technicalsystem_delete",
    ),
    path(
        "technical-systems/<int:pk>/changelog/",
        *changelog(models.TechnicalSystem),
        name="technicalsystem_changelog",
    ),
    path(
        "technical-assets/",
        views.TechnicalAssetListView.as_view(),
        name="technicalasset_list",
    ),
    path(
        "technical-assets/add/",
        views.TechnicalAssetEditView.as_view(),
        name="technicalasset_add",
    ),
    path(
        "technical-assets/<int:pk>/",
        views.TechnicalAssetView.as_view(),
        name="technicalasset",
    ),
    path(
        "technical-assets/<int:pk>/edit/",
        views.TechnicalAssetEditView.as_view(),
        name="technicalasset_edit",
    ),
    path(
        "technical-assets/<int:pk>/delete/",
        views.TechnicalAssetDeleteView.as_view(),
        name="technicalasset_delete",
    ),
    path(
        "technical-assets/<int:pk>/changelog/",
        *changelog(models.TechnicalAsset),
        name="technicalasset_changelog",
    ),
    path(
        "technical-connections/",
        views.TechnicalConnectionListView.as_view(),
        name="technicalconnection_list",
    ),
    path(
        "technical-connections/add/",
        views.TechnicalConnectionEditView.as_view(),
        name="technicalconnection_add",
    ),
    path(
        "technical-connections/<int:pk>/edit/",
        views.TechnicalConnectionEditView.as_view(),
        name="technicalconnection_edit",
    ),
    path(
        "technical-connections/<int:pk>/delete/",
        views.TechnicalConnectionDeleteView.as_view(),
        name="technicalconnection_delete",
    ),
    path(
        "technical-connections/<int:pk>/changelog/",
        *changelog(models.TechnicalConnection),
        name="technicalconnection_changelog",
    ),
]
