"""Solomon Property - REST API."""

from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.register("buildings", views.BuildingViewSet)
router.register("flats", views.FlatViewSet)
router.register("persons", views.PersonViewSet)
router.register("owners", views.PropertyOwnerViewSet)
router.register("flat-owners", views.FlatOwnerViewSet)
router.register("tenants", views.PropertyTenantViewSet)

urlpatterns = router.urls
