import os
import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Note
from .serializers import NoteSerializer
from django.db import models

def translate_text_via_api(text, source='auto', target='hi'):
    # Use LibreTranslate (configurable via env)
    url = os.environ.get('TRANSLATE_API_URL', 'https://libretranslate.com/translate')
    key = os.environ.get('TRANSLATE_API_KEY', '')
    payload = {'q': text, 'source': source, 'target': target, 'format':'text'}
    if key:
        payload['api_key'] = key
    try:
        r = requests.post(url, data=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get('translatedText') or data.get('translation') or None
    except Exception as e:
        # Fallback naive translation (for demo)
        return text[::-1]  # reverse text as a visible fallback

class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all().order_by('-created_at')
    serializer_class = NoteSerializer

    @action(detail=True, methods=['post'])
    def translate(self, request, pk=None):
        note = self.get_object()
        target = request.data.get('target_language', 'hi')
        cache_key = f"translation:{note.id}:{target}"
        cached = cache.get(cache_key)
        if cached:
            return Response({'original': note.text, 'translated': cached, 'cached': True})

        translated = translate_text_via_api(note.text, source=note.original_language or 'auto', target=target)
        if translated is None:
            return Response({'error':'translation_failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        note.translated_text = translated
        note.translated_language = target
        note.translations_count = (note.translations_count or 0) + 1
        note.save()

        # cache it for 10 minutes
        cache.set(cache_key, translated, timeout=600)
        return Response({'original': note.text, 'translated': translated, 'cached': False})

@api_view(['GET'])
def stats_view(request):
    total = Note.objects.count()
    translations = Note.objects.exclude(translated_text__isnull=True).count()
    breakdown_qs = Note.objects.values('original_language').order_by().annotate(count=models.Count('id'))
    breakdown = {item['original_language'] or 'unknown': item['count'] for item in breakdown_qs}
    return Response({'total_notes': total, 'translations_performed': translations, 'by_original_language': breakdown})


from celery.result import AsyncResult
from .tasks import translate_note_task

@action(detail=True, methods=['post'])
def translate_async(self, request, pk=None):
    """Queue an async translation via Celery. Returns task id."""
    note = self.get_object()
    target = request.data.get('target_language', 'hi')
    task = translate_note_task.delay(note.id, target)
    return Response({'task_id': task.id}, status=202)

# Endpoint to check task status (not a viewset action; add separately)
from rest_framework.decorators import api_view
@api_view(['GET'])
def task_status(request, task_id):
    res = AsyncResult(task_id)
    data = {'id': task_id, 'status': res.status, 'result': res.result}
    return Response(data)
