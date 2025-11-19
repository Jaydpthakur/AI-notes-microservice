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

def translate_text_via_api(text, source='en', target='hi'):
    """
    Free translation using MyMemory Translate API (no API key needed).
    """
    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text,
        "langpair": f"{source}|{target}"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        translated = data.get("responseData", {}).get("translatedText")

        if translated:
            return translated

        return None

    except Exception:
        return None

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


from rest_framework.decorators import api_view
@api_view(['POST'])
def legacy_translate(request, note_id):
    """Legacy endpoint /translate/<note_id>/ to match assignment requirement.
    This performs the same synchronous translation as the NoteViewSet.translate action.
    Accepts JSON body: { "target_language": "hi" }"""
    try:
        note = Note.objects.get(id=note_id)
    except Note.DoesNotExist:
        return Response({'error': 'note_not_found'}, status=status.HTTP_404_NOT_FOUND)

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

    cache.set(cache_key, translated, timeout=600)
    return Response({'original': note.text, 'translated': translated, 'cached': False})
