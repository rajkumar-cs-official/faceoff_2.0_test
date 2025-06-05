from django.conf.urls.static import static
from django.conf import settings
from django.urls import path
from .views import Deepfake, Home, UploadVideo, Posture, Eye, Face, AudioTone, HeartRate, HRV, Speech, EyeAnalysisView,MergeVideos
from django.urls import re_path
from django.views.static import serve
import os

# Custom view to add Cache-Control headers for media files
def media_serve(request, path, document_root=None):
    response = serve(request, path, document_root=document_root)
    response["Cache-Control"] = "no-store, max-age=0"  # Prevents caching for media files
    return response

urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('upload-video/', UploadVideo.as_view(), name='upload_video'),
    path('process_deepfake/', Deepfake.as_view(), name='process_deepfake'),  # Make sure it matches exactly
    
    path('process_audio_tone/', AudioTone.as_view(), name='process_audio_tone'),
    path('process-hr/', HeartRate.as_view(), name='process_heart_rate'),
    path('process-hrv/', HRV.as_view(), name='process_heart_rate_variability'),
#    path('process_deepfake_v2/', Deepfake_v2.as_view(), name='process_deepfake_v2'),
    path('process_video_v1/', Posture.as_view(), name='process_video_v1'),
    path('process_speech/', Speech.as_view(), name='process_speech'),
    path('process_video_v2/', Face.as_view(), name='process_video_v2'),
#    #path('process_video_v3/', VideoAnalysisV3.as_view(), name='process_video_v3'),
    path('process_eye/', EyeAnalysisView.as_view(), name='process_eye'),
    path('merged_video/', MergeVideos.as_view(), name='merge_videos'),


    # Add new URL pattern for output files
    re_path(r'^output/(?P<path>.*)$', media_serve, {
        'document_root': os.path.join(settings.MEDIA_ROOT, 'output')
    }),
    
    # Existing media files pattern
    re_path(r'^media/(?P<path>.*)$', media_serve, {'document_root': settings.MEDIA_ROOT}),
]


# # Serve media files in development
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Media URLs with cache control
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', media_serve, {'document_root': settings.MEDIA_ROOT}),
    ]