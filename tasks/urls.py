
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("task/<int:task_id>/", views.task_detail, name="task_detail"),
    path("task/<int:task_id>/start/", views.start_task, name="start_task"),
    path("task/<int:task_id>/updated/", views.mark_updated, name="mark_updated"),
    path("task/<int:task_id>/add-update/", views.add_task_update, name="add_task_update"),
    path("task/<int:task_id>/status/", views.change_task_status, name="change_task_status"),
]
