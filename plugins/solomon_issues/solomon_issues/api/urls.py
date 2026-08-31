from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.register("categories", views.IssueCategoryViewSet)
router.register("tags", views.AssetTagViewSet)
router.register("issues", views.IssueViewSet)
router.register("comments", views.IssueCommentViewSet)
router.register("events", views.IssueEventViewSet)

urlpatterns = router.urls
