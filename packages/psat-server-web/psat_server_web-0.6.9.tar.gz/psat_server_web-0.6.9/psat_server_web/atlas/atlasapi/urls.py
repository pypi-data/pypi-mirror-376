from django.urls import include, path
from rest_framework import routers
from . import views

urlpatterns = [
    path('api/cone/',                  views.ConeView.as_view()),
    path('api/objects/',               views.ObjectsView.as_view()),
    path('api/objectlist/',            views.ObjectListView.as_view()),
    path('api/vrascores/',             views.VRAScoresView.as_view()),
    path('api/vrascoreslist/',         views.VRAScoresListView.as_view()),
    path('api/vratodo/',               views.VRATodoView.as_view()),
    path('api/vratodolist/',           views.VRATodoListView.as_view()),
    path('api/objectgroups/',          views.TcsObjectGroupsView.as_view()),
    path('api/objectgroupslist/',      views.TcsObjectGroupsListView.as_view()),
    path('api/objectgroupsdelete/',    views.TcsObjectGroupsDeleteView.as_view()),
    path('api/vrarank/',               views.VRARankView.as_view()),
    path('api/vraranklist/',           views.VRARankListView.as_view()),
    path('api/externalxmlist/',        views.ExternalCrossmatchesListView.as_view()),
    path('api/auth-token/',            views.ObtainExpiringAuthToken.as_view(), name='auth_token'),
    path('api/objectdetectionlist/',   views.ObjectDetectionListView.as_view()),
]
