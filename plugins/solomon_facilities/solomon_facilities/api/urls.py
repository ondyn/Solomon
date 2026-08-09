from netbox.api.routers import NetBoxRouter

from . import views


router = NetBoxRouter()
router.register("levels", views.BuildingLevelViewSet)
router.register("floor-plans", views.FloorPlanViewSet)
router.register("plan-revisions", views.PlanRevisionViewSet)
router.register("spaces", views.SpaceViewSet)
router.register("space-assignments", views.SpaceFlatAssignmentViewSet)
router.register("space-usages", views.SpaceUsageViewSet)
router.register("doors", views.DoorViewSet)
router.register("locks", views.LockCylinderViewSet)
router.register("key-profiles", views.KeyProfileViewSet)
router.register("keys", views.KeyCopyViewSet)
router.register("key-issues", views.KeyIssueViewSet)
router.register("technical-systems", views.TechnicalSystemViewSet)
router.register("technical-assets", views.TechnicalAssetViewSet)
router.register("technical-connections", views.TechnicalConnectionViewSet)
router.register("plan-elements", views.PlanElementViewSet)

urlpatterns = router.urls
