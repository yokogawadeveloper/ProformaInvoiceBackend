from rest_framework import routers
from excelupload.views import proformaItemMasterViewSet, proformaMasterViewSet, proformaItemViewSet
from orderack.views import orderAcknowledgementViewSet, orderAcknowledgementHistoryViewSet, orderAckViewSet
from masterdata.views import divisionMasterViewSet, categoryMasterViewSet, regionMasterViewSet, projectManagerMasterViewSet
from users.views import UsersViewSet

router = routers.DefaultRouter()

router.register(r'user_list', UsersViewSet, basename="UserList")
router.register(r'proforma_master_list', proformaItemMasterViewSet, basename="ProformaItemMaster")
router.register(r'get_proforma_master', proformaMasterViewSet, basename="ProformaMaster")
router.register(r'proforma_item_list', proformaItemViewSet, basename="ProformaItem")

router.register(r'get_order_ack', orderAcknowledgementViewSet, basename="OrderAck")
router.register(r'order_ack_list', orderAckViewSet, basename="OrderAcknowledgement")
router.register(r'get_order_ack_history', orderAcknowledgementHistoryViewSet, basename="OrderAckHistory")

router.register(r'division_master_list', divisionMasterViewSet, basename="DivisionMaster")
router.register(r'category_master_list', categoryMasterViewSet, basename="CategoryMaster")
router.register(r'region_master_list', regionMasterViewSet, basename="RegionMaster")
router.register(r'projectmanager_master_list', projectManagerMasterViewSet, basename="ProjectManagerMaster")


