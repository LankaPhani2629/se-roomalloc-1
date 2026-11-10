from django.urls import path
from . import views

urlpatterns = [
    path('structures/', views.fee_structures_view, name='fee_structures'),
    path('record-payment/', views.record_payment_view, name='record_payment'),
    path('pending-dues/', views.pending_dues_view, name='pending_dues'),
    path('history/', views.payment_history_view, name='payment_history'),
    path('receipt/<int:pk>/', views.receipt_detail_view, name='receipt_detail'),
    path('my-fees/', views.student_fees_view, name='student_fees'),
]

