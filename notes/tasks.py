from django.core.cache import cache
from celery import shared_task
from .models import Note
from .views import translate_text_via_api

@shared_task
def translate_note_task(note_id, target_language='hi'):
    try:
        note = Note.objects.get(id=note_id)
    except Note.DoesNotExist:
        return None
    translated = translate_text_via_api(note.text, source=note.original_language or 'auto', target=target_language)
    if translated:
        note.translated_text = translated
        note.translated_language = target_language
        note.translations_count = (note.translations_count or 0) + 1
        note.save()
        cache.set(f"translation:{note.id}:{target_language}", translated, timeout=600)
    return translated
